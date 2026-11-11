"""Create the "Demo Co" demo workspace with synthetic fixture data (no real people).

Usage: python tools/make_demo.py [target_dir]     (default: demo/)
Copies templates/workspace, then writes brand/catalog/funnel/channels/keywords config, approved knowledge,
and made-up runs, conversations, leads and risk logs so the scripts and the control center have data.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "plugins" / "social-seeding" / "templates" / "workspace"

BRAND = '''[brand]
brand_name = "Demo Co"
rep_name = "Dana Demo"
disclosure = "I am {rep}, from {brand}."
owner_email = "owner@example.com"
ui_language = "en"
audience_timezone = "Europe/Madrid"
operator_timezone = "Asia/Ho_Chi_Minh"
control_center_url = ""
'''
CATALOG = '''[[category]]
id = "home"
label = "Home goods"
keywords = ["detergent", "soap", "kitchenware"]

[[category]]
id = "build"
label = "Building materials"
keywords = ["cement", "tiles", "paint"]
'''
FUNNEL = '''[destination.home]
type = "whatsapp"
name = "Demo Co - Home goods"
url = "https://chat.whatsapp.com/DEMOHOME0000000000000"
covers = ["detergent", "soap"]
tracked_base = ""

[destination.build]
type = "telegram"
name = "Demo Co - Building"
url = "https://t.me/democo_build"
covers = ["cement", "tiles"]
tracked_base = "https://example.com/go/build?src={channel}"

[[member_count]]
date = "2026-01-05"
home = 10
build = 4
note = "baseline"

[[member_count]]
date = "2026-01-12"
home = 16
build = 5
note = "week 1"
'''
KEYWORDS = '''[demand]
en = ["looking for", "need a supplier", "who sells", "wholesale"]
es = ["busco", "necesito", "quien vende"]

[category.home]
en = ["detergent", "soap"]
es = ["detergente", "jabon"]

[category.build]
en = ["cement", "tiles"]
es = ["cemento", "azulejos"]

[signals.qualified]
en = ["price", "how much", "minimum", "contact"]
es = ["precio", "cuanto", "minimo"]

[signals.negative]
en = ["spam", "not interested", "scam"]
es = ["spam", "no me interesa", "estafa"]

[cities]
en = ["Anytown", "Springfield"]
'''
CAPS_LANGS = '''[languages]
"en" = { native_review_done = true, reviewer = "Demo owner" }
"es" = { native_review_done = false, reviewer = "" }
'''
CHANNELS = '''[[channel]]
id = "A1"
name = "Anytown Small Business Owners"
url = "https://www.facebook.com/groups/1000000000001"
kind = "discussion"
identity = "personal"
language = "en"
fit = ["home", "build"]
city = "Anytown"
members = 12000
posts_per_day = 12
promo_posts = "unknown"
links = "no"
rules = "On-topic only. No spam."
wave = "pilot"
state = "active"
joined_on = "2026-01-05"

[[channel]]
id = "B1"
name = "Springfield Wholesale Board"
url = "https://www.facebook.com/groups/1000000000002"
kind = "board"
identity = "personal"
language = "es"
fit = ["home"]
city = "Springfield"
members = 54000
posts_per_day = 90
promo_posts = "yes"
links = "no"
rules = "Buyers and sellers. One offer post per day."
wave = "pilot"
state = "active"
joined_on = "2026-01-05"

[[channel]]
id = "P1"
name = "Demo Hardware Fans (fanpage)"
url = "https://www.facebook.com/demohardwarefans"
kind = "page"
identity = "personal"
language = "en"
fit = ["build"]
city = "Anytown"
members = 3400
posts_per_day = 2
promo_posts = "no"
links = "unknown"
rules = "Comments welcome."
wave = "w2"
state = "pending"
joined_on = ""
'''
KNOW = {
    "company.md": "Demo Co supplies home goods and building materials to small shops.\n",
    "products/home.md": "Demo Co sells laundry detergent and dish soap by the pallet.\n",
    "products/build.md": "Demo Co sells cement and floor tiles by the pallet.\n",
    "faq.md": "Prices and payment terms depend on volume. [CONFIRM] Delivery regions.\n",
}


def conv(cid, channel, stage, maxs, cat, name, opened, nxt, closed=""):
    return f'''---
id: {cid}
channel: {channel}
thread_url: https://www.facebook.com/groups/1000000000001/posts/{cid[-3:]}
identity: personal
playbook: sales-promo
category: {cat}
stage: {stage}
max_stage: {maxs}
counterpart: "{name}"
province: "Anytown"
unanswered_turns: 0
opened: {opened}
last_checked: {opened}
next_move: "{nxt}"
closed_reason: "{closed}"
---

## Thread summary
Fixture conversation.
'''


def main(target: str = "demo") -> int:
    out = Path(target)
    if not out.is_absolute():
        out = REPO / out
    for sub in ("runs", "conversations", "risk", "status"):
        shutil.rmtree(out / sub, ignore_errors=True)
    shutil.copytree(TEMPLATE, out, dirs_exist_ok=True)
    cfg = out / "config"
    (cfg / "brand.toml").write_text(BRAND, encoding="utf-8")
    (cfg / "catalog.toml").write_text(CATALOG, encoding="utf-8")
    (cfg / "funnel.toml").write_text(FUNNEL, encoding="utf-8")
    (cfg / "channels.toml").write_text(CHANNELS, encoding="utf-8")
    (cfg / "keywords.toml").write_text(KEYWORDS, encoding="utf-8")
    caps = (cfg / "caps.toml").read_text(encoding="utf-8")
    caps = caps.split("[languages]")[0] + CAPS_LANGS
    (cfg / "caps.toml").write_text(caps, encoding="utf-8")
    for rel, body in KNOW.items():
        p = out / "knowledge" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        status = "APPROVED (Demo owner, 2026-01-05)" if rel != "faq.md" else "DRAFT"
        p.write_text(f"---\nstatus: {status}\nvalid_from: 2026-01-05\nvalid_to:\n---\n# {rel}\n- {body}", encoding="utf-8")

    today = dt.date.today()
    d1, d2 = (today - dt.timedelta(days=2)).isoformat(), (today - dt.timedelta(days=1)).isoformat()
    convs = [("c-001", "A1", 0, 0, "home", "Alex Sample", d1, "seed reply: ask volume", ""),
             ("c-002", "A1", 1, 1, "build", "Bea Example", d1, "ask province", ""),
             ("c-003", "B1", 2, 2, "home", "Cy Fixture", d1, "offer invite", ""),
             ("c-004", "B1", 3, 3, "home", "Di Placeholder", d2, "wait for join", ""),
             ("c-005", "A1", 4, 4, "build", "Eli Mock", d2, "close", ""),
             ("c-006", "A1", "X", 1, "build", "Fay Stub", d2, "none", "2 unanswered turns")]
    (out / "conversations").mkdir(exist_ok=True)
    for c in convs:
        (out / "conversations" / f"{c[0]}.md").write_text(conv(*c), encoding="utf-8")

    for d, n_items in ((d1, 3), (d2, 4)):
        rd = out / "runs" / d
        rd.mkdir(parents=True)
        threads = [{"channel": "A1", "score": 2}, {"channel": "B1", "score": 3}, {"channel": "A1", "score": 1}]
        (rd / "scan.json").write_text(json.dumps({
            "mode": "draft-only", "channels_scanned": ["A1", "B1"], "posts_read": {"A1": 50, "B1": 50},
            "threads": threads, "rejected_matches": [{"channel": "B1", "why": "seller ad, not a buyer post"}],
            "notes": "fixture"}), encoding="utf-8")
        items = [{"n": i, "channel": "A1" if i % 2 else "B1", "group": "Demo group", "type": "comment",
                  "category": "home", "activity": "12 posts/day", "text": f"Fixture reply {i} to a buyer post.",
                  "meaning": f"Fixture meaning {i}", "time": f"{9 + i}:00", "url": "https://www.facebook.com/groups/1000000000001"}
                 for i in range(1, n_items + 1)]
        (rd / "queue.json").write_text(json.dumps({"date": d, "title": "Demo Co queue", "author": "Dana Demo",
                                                   "health": {"personal": "GREEN", "mode": "draft-only"},
                                                   "checks": "Facts OK; caps OK", "items": items}), encoding="utf-8")
        (rd / "approval.md").write_text("- #1\n- #2\n", encoding="utf-8")
    with open(out / "runs" / d1 / "post-log.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datetime", "channel", "type", "status", "has_link", "target_url", "posted_url"])
        w.writerow([f"{d1}T10:00:00", "A1", "comment", "posted", "false", "https://www.facebook.com/groups/1/posts/1", "https://www.facebook.com/groups/1/posts/1?c=1"])
        w.writerow([f"{d1}T11:00:00", "B1", "post", "posted", "false", "https://www.facebook.com/groups/2", ""])
    with open(out / "leads.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "profile_url", "channel", "category", "contact", "date"])
        w.writerow(["Cy Fixture", "https://www.facebook.com/cy.fixture", "B1", "home", "+00 000 000 001", d1])
    (out / "risk").mkdir(exist_ok=True)
    (out / "risk" / "health-personal.md").write_text(
        f"# Health log\n\n## {d1} 08:00 - GREEN\n- account status: ok\n- notifications: none\n- visibility: comments visible\n- action: none\n\n"
        f"## {d2} 08:00 - AMBER\n- account status: ok\n- notifications: 1 removed post\n- visibility: ok\n- action: halve caps\n", encoding="utf-8")
    (out / "risk" / "incidents.md").write_text(
        "| Date | Identity | What | Action |\n|---|---|---|---|\n"
        f"| {d2} | personal | 1 post removed in B1 | caps halved 72h |\n", encoding="utf-8")
    print(f"demo workspace: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
