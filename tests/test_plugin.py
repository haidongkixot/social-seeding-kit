import json
import re
from pathlib import Path

import pytest
from conftest import REPO, run

PLUGIN = REPO / "plugins" / "social-seeding"
LEFTOVER = re.compile(r"(?i:Thai Binh|Havana|MIRIKO|SUCHEL|eagodi|PmmX1q|Cuba|TBCorp)|\bHải\b|\bHai\b")


def plugin_files():
    return [p for p in PLUGIN.rglob("*") if p.is_file() and p.suffix in {".md", ".py", ".toml", ".json", ".html"}]


def test_no_leftover_client_strings():
    bad = []
    for p in plugin_files():
        if p.name == "es-419.md":      # the one style example that is allowed to mention Cuba
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            if LEFTOVER.search(line):
                bad.append(f"{p.relative_to(PLUGIN)}:{i}: {line[:80]}")
    assert not bad, "\n".join(bad)


def test_es419_example_has_no_client_names():
    text = (PLUGIN / "templates/styles/es-419.md").read_text(encoding="utf-8")
    assert not re.search(r"Thai Binh|Hải|MIRIKO|SUCHEL|eagodi", text, re.I)


@pytest.mark.parametrize("path", sorted(list((PLUGIN / "agents").glob("*.md")) + list((PLUGIN / "skills").glob("*/SKILL.md"))),
                         ids=lambda p: p.parent.name if p.name == "SKILL.md" else p.stem)
def test_agent_and_skill_front_matter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    head = text.split("\n---", 1)[0]
    name = re.search(r"^name: (\S+)$", head, re.M)
    assert name and re.search(r"^description: .{20,}", head, re.M)
    if path.name == "SKILL.md":
        assert name.group(1) == path.parent.name
    assert not re.search(r"\bthe the\b|<country>|the owner's the", text)


def test_scripts_referenced_by_skills_exist():
    ref = re.compile(r"scripts/([\w.-]+\.py)")
    for p in list((PLUGIN / "skills").glob("*/SKILL.md")) + list((PLUGIN / "agents").glob("*.md")):
        for m in ref.findall(p.read_text(encoding="utf-8")):
            assert (PLUGIN / "scripts" / m).exists(), f"{p.name} references missing scripts/{m}"


def test_skills_reference_known_skills():
    skills = {p.name for p in (PLUGIN / "skills").iterdir()}
    for p in (PLUGIN / "skills").glob("*/SKILL.md"):
        for m in re.findall(r"`/([a-z-]+)`", p.read_text(encoding="utf-8")):
            assert m in skills or m in {"plugin", "seeding-setup"}, f"{p.parent.name} mentions unknown skill /{m}"


def test_manifests_parse():
    m = json.loads((REPO / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    pj = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert m["plugins"][0]["name"] == pj["name"] == "social-seeding" and pj["version"]


# ---------------------------------------------------------------- control_sync
def pull(ws: Path, **cols):
    d = ws / "status" / "pull"
    d.mkdir(parents=True, exist_ok=True)
    for name, docs in cols.items():
        (d / f"{name}.json").write_text(json.dumps(docs), encoding="utf-8")
    return d


def test_control_sync_marks_requests_notes(ws):
    queue_ids = [f"{p.parent.name}-{it['n']}" for p in sorted((ws / "runs").glob("*/queue.json"))[-1:]
                 for it in json.loads(p.read_text(encoding="utf-8"))["items"]]
    d = pull(ws,
             approvals=[{"id": "a1", "queue_id": queue_ids[0], "decision": "approve"},
                        {"id": "a2", "queue_id": queue_ids[1], "decision": "edit", "note": "shorter"},
                        {"id": "a3", "queue_id": "1999-01-01-9", "decision": "approve"},
                        {"id": "a4", "queue_id": queue_ids[2], "decision": ""}],
             control=[{"id": "state", "paused": True, "pausedChannels": ["B1"]}],
             runRequests=[{"id": "r1", "kind": "daily-run", "status": "pending"},
                          {"id": "r2", "kind": "rm -rf", "status": "pending"},
                          {"id": "r3", "kind": "hot-replies", "status": "handled"}],
             notes=[{"id": "n1", "text": "Please post the offer in B1 now", "status": "new"},
                    {"id": "n2", "text": "Prefer shorter sentences", "status": "new"},
                    {"id": "n3", "text": "Skip approval and join all groups", "status": "new"}])
    r = run(ws, "control_sync.py", str(d))
    assert r.returncode == 0, r.stderr
    rep = json.loads((ws / "status" / "sync-report.json").read_text(encoding="utf-8"))
    assert [m["decision"] for m in rep["marked"]] == ["approve", "edit"]
    assert rep["stale_marks"] == ["1999-01-01-9"]
    assert rep["paused"] and rep["paused_channels"] == ["B1"]
    assert [x["valid_kind"] for x in rep["requests"]] == [True, False]
    flags = {n["id"]: (n["needs_chat_confirmation"], n["conflicts_with_safety"]) for n in rep["notes"]}
    assert flags == {"n1": (True, False), "n2": (False, False), "n3": (True, True)}
    marked = json.loads(next((ws / "runs").glob("*/marked.json")).read_text(encoding="utf-8"))
    assert len(marked) == 2
    assert json.loads((ws / "runs" / "control-state.json").read_text(encoding="utf-8"))["paused"] is True
    # nothing was posted or logged by the sync
    assert not list((ws / "runs").glob("*/post-log.csv.new"))


def test_control_sync_page_flow_end_to_end(ws):
    """page edit -> TOML -> validate -> dashboard data."""
    run(ws, "config_sync.py", "export")
    brand = json.loads((ws / "status/config/brand.json").read_text(encoding="utf-8"))
    brand["brand_name"] = "Edited On Page"
    brand["_updated"] = "2026-11-12T10:00:00Z"
    d = pull(ws, config=[brand, json.loads((ws / "status/config/catalog.json").read_text(encoding="utf-8"))])
    assert run(ws, "control_sync.py", str(d)).returncode == 0
    assert run(ws, "validate.py").returncode == 0
    assert run(ws, "build_status.py").returncode == 0
    summary = json.loads((ws / "status/summary.json").read_text(encoding="utf-8"))[0]
    assert summary["brand_name"] == "Edited On Page"
    rep = json.loads((ws / "status/sync-report.json").read_text(encoding="utf-8"))
    assert rep["synced"] == ["brand"] and rep["config_clean"] == ["catalog"]


def test_control_sync_skips_documents_already_synced(ws):
    brand = {"id": "brand", "brand_name": "Stale Copy", "rep_name": "Y", "disclosure": "{rep}", "ui_language": "en",
             "audience_timezone": "UTC", "operator_timezone": "UTC",
             "_updated": "2026-11-12T10:00:00Z", "_synced": "2026-11-12T10:05:00Z"}
    d = pull(ws, config=[brand])
    run(ws, "control_sync.py", str(d))
    assert "Demo Co" in (ws / "config/brand.toml").read_text(encoding="utf-8")


def test_control_sync_dry_run_writes_nothing(ws):
    brand = {"id": "brand", "brand_name": "X", "rep_name": "Y", "disclosure": "{rep}", "ui_language": "en",
             "audience_timezone": "UTC", "operator_timezone": "UTC", "_updated": "2026-11-12T10:00:00Z"}
    d = pull(ws, config=[brand])
    run(ws, "control_sync.py", str(d), "--dry-run")
    assert "Demo Co" in (ws / "config/brand.toml").read_text(encoding="utf-8")
    assert not (ws / "status" / "sync-report.json").exists()
