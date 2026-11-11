import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from conftest import REPO, SCRIPTS, run

SETUP = str(SCRIPTS / "setup_workspace.py")


def setup(*args, cwd=None):
    return subprocess.run([sys.executable, SETUP, *args], capture_output=True, text=True, encoding="utf-8", cwd=cwd)


def init_demo(tmp_path, *extra):
    ws = tmp_path / "demo-co"
    r = setup("init", str(ws), "--brand", "Demo Co", "--rep", "Dana Demo", "--language", "en",
              "--audience-tz", "Europe/Madrid", "--operator-tz", "Asia/Ho_Chi_Minh", "--owner-email", "owner@example.com",
              "--lang-codes", "en,es-419", "--category", "home=Home goods", "--category", "build=Building materials", *extra)
    assert r.returncode == 0, r.stderr
    return ws


def test_prereqs_reports_each_requirement():
    r = setup("prereqs")
    out = json.loads(r.stdout)
    assert {"python", "openpyxl", "Pillow", "git", "browser", "timezones", "manual"} <= set(out)
    assert out["python"]["ok"]


def test_init_creates_a_valid_git_workspace(tmp_path):
    ws = init_demo(tmp_path)
    r = run(ws, "validate.py")
    assert r.returncode == 0, r.stdout
    brand = tomllib.loads((ws / "config/brand.toml").read_text(encoding="utf-8"))["brand"]
    assert brand["brand_name"] == "Demo Co" and brand["audience_timezone"] == "Europe/Madrid" and brand["owner_email"] == "owner@example.com"
    assert [c["id"] for c in tomllib.loads((ws / "config/catalog.toml").read_text(encoding="utf-8"))["category"]] == ["home", "build"]
    langs = tomllib.loads((ws / "config/caps.toml").read_text(encoding="utf-8"))["languages"]
    assert set(langs) == {"en", "es-419"} and not langs["es-419"]["native_review_done"]
    kw = tomllib.loads((ws / "config/keywords.toml").read_text(encoding="utf-8"))
    assert set(kw["category"]) == {"home", "build"} and set(kw["demand"]) == {"en", "es-419"}
    assert (ws / "playbooks/sales-promo.md").exists() and (ws / "playbooks/es-419-style.md").exists() and (ws / "playbooks/en-style.md").exists()
    assert (ws / ".git").exists()
    ignored = (ws / ".gitignore").read_text(encoding="utf-8")
    assert all(x in ignored for x in ("runs/", "conversations/", "leads.csv", "reports/"))
    log = subprocess.run(["git", "log", "--oneline"], cwd=ws, capture_output=True, text=True).stdout
    assert "Initial workspace" in log


def test_init_refuses_a_non_empty_folder(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "file.txt").write_text("hi", encoding="utf-8")
    r = setup("init", str(tmp_path / "x"))
    assert r.returncode == 1 and "not empty" in r.stderr


def test_schedule_converts_between_timezones(tmp_path):
    ws = init_demo(tmp_path)
    r = setup("schedule", "--workspace", str(ws))
    assert r.returncode == 0, r.stderr
    jobs = {j["job"]: j for j in json.loads(r.stdout)["jobs"]}
    assert jobs["daily_run"]["cron_operator_tz"] == "0 8 * * *"
    assert jobs["daily_run"]["audience_time"] in ("02:00", "03:00")        # Vietnam 08:00 is the small hours in Madrid
    assert jobs["check_replies"]["operator_time"] == "20:00-07:00"
    assert jobs["check_replies"]["cron_operator_tz"] == "7 20-23,0-7 * * *"


# ---------------------------------------------------------------- the first day on a fresh workspace (draft-only, no Facebook)
def test_fresh_workspace_first_draft_only_day(tmp_path):
    """Demo Co, one test group: the files /daily-run --draft-only leaves behind feed the scripts end to end."""
    ws = init_demo(tmp_path)
    ch = {"id": "channels", "channels": [{
        "id": "T1", "name": "Test Group", "url": "https://www.facebook.com/groups/42424242", "kind": "discussion", "identity": "personal",
        "language": "en", "fit": ["home"], "city": "Anytown", "members": 500, "posts_per_day": 5, "promo_posts": "unknown",
        "links": "no", "rules": "Be kind.", "wave": "pilot", "state": "active", "joined_on": "2026-11-01"}]}
    (ws / "bundle.json").write_text(json.dumps({"channels": ch}), encoding="utf-8")
    assert run(ws, "config_sync.py", "apply", "bundle.json").returncode == 0
    day = ws / "runs" / "2026-11-12"
    day.mkdir(parents=True)
    (day / "scan.json").write_text(json.dumps({"mode": "draft-only", "channels_scanned": ["T1"], "posts_read": {"T1": 50},
                                               "threads": [{"channel": "T1", "score": 3}], "notes": "draft-only"}), encoding="utf-8")
    items = [{"n": 1, "type": "reply", "channel": "T1", "identity": "personal", "group": "Test Group", "category": "home",
              "language": "en", "text": "I am Dana Demo, from Demo Co. What quantity do you need?", "meaning": "Same in English.",
              "time": "10:00", "url": "https://www.facebook.com/groups/42424242", "target_url": "https://www.facebook.com/groups/42424242/posts/1",
              "stage_from": 0, "stage_to": 1, "draft_only": True, "review": {"verdict": "PASS"}, "risk": {"verdict": "PASS"},
              "why": "Buyer post.", "thread_summary": "OP wants detergent."}]
    (day / "queue.json").write_text(json.dumps({"date": "2026-11-12", "title": "Demo Co queue", "author": "Dana Demo",
                                                "health": {"personal": "GREEN", "mode": "draft-only"}, "checks": "ok", "items": items}), encoding="utf-8")
    assert run(ws, "validate.py").returncode == 0
    assert run(ws, "build_review.py", str(day)).returncode == 0
    review = (day / "review.html").read_text(encoding="utf-8")
    assert "Draft only" in review and "What quantity" in review
    x = run(ws, "build_queue_xlsx.py", str(day / "queue.json"), "--no-previews")
    assert x.returncode == 0, x.stderr
    assert (day / "queue.xlsx").exists()
    assert run(ws, "build_status.py").returncode == 0
    q = json.loads((ws / "status/queue.json").read_text(encoding="utf-8"))
    assert q[0]["draft_only"] is True and q[0]["id"] == "2026-11-12-1"
    groups = json.loads((ws / "status/groups.json").read_text(encoding="utf-8"))
    assert groups[0]["id"] == "T1" and groups[0]["state"] == "active"
