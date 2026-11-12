"""Compile the workspace state into status/<collection>.json files for the control center.

Usage: python scripts/build_status.py

Each file is a JSON list of documents (every document has an "id"), one file per collection of the
control center's database, plus status/index.json (collection -> count, generated_at). The
sync-control skill writes them to the artifact database with one ArtifactData batch.
Stdlib only. Personal data comes only from leads.csv: public names of people who engaged, and the
contact a person gave us themselves.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, brand, categories, front_matter, load_toml  # noqa: E402

STAGE = {"0": "SEED", "1": "ENGAGED", "2": "QUALIFIED", "3": "INVITED", "4": "JOINED", "X": "CLOSED"}


def read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def post_log() -> list[dict]:
    rows = []
    for f in sorted((ROOT / "runs").glob("*/post-log.csv")):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh), start=1):
                row = {k: (v or "") for k, v in r.items() if k}
                row["date"] = f.parent.name
                row["url"] = row.get("posted_url") or row.get("target_url", "")
                row["id"] = f"{f.parent.name}-{i:03d}"
                rows.append(row)
    return rows


def conversations() -> list[dict]:
    out = []
    for f in sorted((ROOT / "conversations").glob("*.md")):
        fm, _ = front_matter(f)
        if not fm.get("id"):
            continue
        st = str(fm.get("stage", "0"))
        out.append({"id": fm["id"], "channel": fm.get("channel", ""), "thread_url": fm.get("thread_url", ""),
                    "stage": st, "stage_name": STAGE.get(st, st), "max_stage": fm.get("max_stage", st),
                    "category": fm.get("category", ""), "playbook": fm.get("playbook", ""),
                    "counterpart": fm.get("counterpart", ""), "province": fm.get("province", ""),
                    "unanswered_turns": int(fm.get("unanswered_turns", "0") or 0),
                    "opened": fm.get("opened", ""), "last_checked": fm.get("last_checked", ""),
                    "next_move": fm.get("next_move", ""), "closed_reason": fm.get("closed_reason", "")})
    return out


def health() -> list[dict]:
    out = []
    for f in sorted((ROOT / "risk").glob("health-*.md")):
        ident = f.stem.removeprefix("health-")
        for block in re.split(r"\n(?=## )", f.read_text(encoding="utf-8")):
            m = re.match(r"## (\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))? - (GREEN|AMBER|RED)", block)
            if not m:
                continue
            fields = dict(re.findall(r"^- ([a-z ]+): (.*)$", block, re.M))
            out.append({"id": f"{m.group(1)}-{(m.group(2) or '00:00').replace(':', '')}-{ident}", "date": m.group(1),
                        "identity": ident, "rating": m.group(3),
                        "account": fields.get("account status", ""), "notifications": fields.get("notifications", ""),
                        "visibility": fields.get("visibility", ""), "action": fields.get("action", "")})
    return out


def incidents() -> list[dict]:
    p = ROOT / "risk" / "incidents.md"
    rows = []
    if p.exists():
        lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
        if len(lines) > 2:
            head = [h.strip().lower().replace(" ", "_") for h in lines[0].strip("|").split("|")]
            for i, l in enumerate(lines[2:], start=1):
                cells = [c.strip() for c in l.strip("|").split("|")]
                if any(cells):
                    rows.append({"id": f"inc-{i:03d}", **dict(zip(head, cells))})
    return rows


def queue_items(run_dirs: list[Path], keep: int = 3) -> list[dict]:
    """Items of the newest queues (morning and -pm), for the control center's Approvals tab."""
    out = []
    for d in run_dirs[-keep:]:
        for f in sorted(d.glob("queue*.json")):
            q = read_json(f, {})
            items = q.get("items", []) if isinstance(q, dict) else q
            tag = f.stem.removeprefix("queue")          # "" or "-pm"
            for it in items:
                out.append({"id": f"{d.name}{tag}-{it.get('n')}", "date": d.name, "queue": f.stem, "n": it.get("n"),
                            "channel": it.get("channel", ""), "type": it.get("type", ""),
                            "category": it.get("category", ""), "language": it.get("language", ""),
                            "text": it.get("text", ""), "meaning": it.get("meaning", it.get("vi", "")),
                            "target_url": it.get("target_url", it.get("url", "")),
                            "time": it.get("time", ""), "why": it.get("why", ""),
                            "stage_from": it.get("stage_from"), "stage_to": it.get("stage_to"),
                            "has_link": bool(it.get("has_link", False)), "draft_only": bool(it.get("draft_only", False)),
                            "review": it.get("review", {}).get("verdict", ""), "risk": it.get("risk", {}).get("verdict", "")})
    return out


def readiness(caps: dict, funnel: dict, chans: list[dict], knowledge: list[dict], br: dict, cats: list[dict]) -> list[dict]:
    langs = caps.get("languages", {})
    unreviewed = [k for k, v in langs.items() if not v.get("native_review_done")]
    dest = funnel.get("destination", {})
    missing_dest = [c["id"] for c in cats if not dest.get(c["id"], {}).get("url")]
    approved = sum(1 for k in knowledge if k["status"] == "APPROVED")
    confirms = [k for k in knowledge if k["open_confirms"]]
    active = sum(1 for c in chans if c.get("state") == "active")
    counts = funnel.get("member_count", [])
    real = [m for m in counts if any(m.get(c["id"]) for c in cats)]
    tracked = bool(dest) and all(d.get("tracked_base") for d in dest.values())
    rows = [
        ("Facts", "Knowledge docs approved", approved > 0 and approved >= len(knowledge), f"{approved} of {len(knowledge)} approved"),
        ("Facts", "Open [CONFIRM] questions", not confirms,
         "; ".join(f"{Path(k['file']).name}: {k['open_confirms']}" for k in confirms) or "none"),
        ("Language", "Native review of each language", not unreviewed, ", ".join(unreviewed) or "all reviewed"),
        ("Funnel", "Destination for every category", not missing_dest, ", ".join(missing_dest) or "all set"),
        ("Measurement", "Member counts entered", bool(real), f"{len(real)} counts" if real else "baseline still empty"),
        ("Measurement", "Click tracking links", tracked, "set" if tracked else "not set up"),
        ("Channels", "At least one channel joined and active", active > 0, f"{active} active of {len(chans)}"),
        ("Control", "Control center published", bool(br.get("control_center_url")), br.get("control_center_url", "")),
    ]
    return [{"id": f"r{i}", "area": a, "item": it, "status": "done" if ok else "open", "detail": d}
            for i, (a, it, ok, d) in enumerate(rows, start=1)]


def main() -> int:
    today = dt.date.today()
    caps = load_toml("caps.toml")
    br = brand()
    cats = categories()
    funnel = load_toml("funnel.toml")
    warm = int(caps["per_group"]["warmup_days"])
    chans = load_toml("channels.toml").get("channel", [])
    posts = post_log()
    convs = conversations()

    runs, scans, rejected = [], [], []
    last_scan: dict[str, dict] = {}
    run_dirs = sorted(p for p in (ROOT / "runs").iterdir() if p.is_dir()) if (ROOT / "runs").exists() else []
    for d in run_dirs:
        scan = read_json(d / "scan.json", {})
        q = read_json(d / "queue.json", {})
        items = q.get("items", []) if isinstance(q, dict) else q
        health_hdr = q.get("health", {}) if isinstance(q, dict) else {}
        approval = d / "approval.md"
        approved = len(re.findall(r"^\s*-\s*#?\d+", approval.read_text(encoding="utf-8"), re.M)) if approval.exists() else 0
        posted = sum(1 for p in posts if p.get("date") == d.name)
        reads = scan.get("posts_read", {})
        runs.append({"id": d.name, "date": d.name, "mode": scan.get("mode", health_hdr.get("mode", "")),
                     "health": health_hdr.get("personal", ""), "channels_scanned": len(scan.get("channels_scanned", [])),
                     "posts_read": sum(reads.values()) if reads else 0, "candidates": len(scan.get("threads", [])),
                     "items_queued": len(items), "items_approved": approved, "items_posted": posted,
                     "notes": scan.get("notes", "")})
        for ch, n in reads.items():
            cands = sum(1 for t in scan.get("threads", []) if t.get("channel") == ch)
            row = {"id": f"{d.name}-{ch}", "date": d.name, "channel": ch, "posts_read": n, "candidates": cands}
            scans.append(row)
            last_scan[ch] = row
        for i, r in enumerate(scan.get("rejected_matches", []), start=1):
            rejected.append({"id": f"{d.name}-{i:03d}", "date": d.name, "channel": r.get("channel", ""), "why": r.get("why", "")})

    groups = []
    for c in chans:
        joined = c.get("joined_on", "")
        warm_until = (dt.date.fromisoformat(joined) + dt.timedelta(days=warm)).isoformat() if joined else ""
        cid = c["id"]
        ls = last_scan.get(cid, {})
        groups.append({"id": cid, "name": c.get("name", ""), "url": c.get("url", ""), "kind": c.get("kind", ""),
                       "fit": ", ".join(c.get("fit", [])), "city": c.get("city", ""), "members": c.get("members", 0),
                       "language": c.get("language", ""), "posts_per_day": c.get("posts_per_day", 0),
                       "wave": c.get("wave", ""), "state": c.get("state", ""),
                       "joined_on": joined, "warmup_until": warm_until,
                       "in_warmup": bool(warm_until) and today.isoformat() < warm_until,
                       "promo_posts": c.get("promo_posts", ""), "links": c.get("links", ""),
                       "items_posted": sum(1 for p in posts if p.get("channel") == cid),
                       "open_conversations": sum(1 for v in convs if v["channel"] == cid and v["stage"] != "X"),
                       "last_scan": ls.get("date", ""), "last_scan_posts": ls.get("posts_read", 0)})

    knowledge = []
    for f in sorted((ROOT / "knowledge").rglob("*.md")) if (ROOT / "knowledge").exists() else []:
        if f.name == "README.md":
            continue
        fm, body = front_matter(f)
        rel = f.relative_to(ROOT).as_posix()
        knowledge.append({"id": rel.replace("/", "__"), "file": rel, "status": (fm.get("status", "") or "").split(" ")[0],
                          "status_detail": fm.get("status", ""), "open_confirms": body.count("[CONFIRM")})

    ids = ["0", "1", "2", "3", "4", "X"]
    funnel_rows = [{"id": st, "stage": st, "stage_name": STAGE[st],
                    "now": sum(1 for v in convs if v["stage"] == st),
                    "ever": (sum(1 for v in convs if v["max_stage"] != "X" and v["max_stage"] >= st) if st != "X"
                             else sum(1 for v in convs if v["stage"] == "X"))} for st in ids]

    leads = []
    lp = ROOT / "leads.csv"
    if lp.exists():
        with open(lp, encoding="utf-8-sig", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh), start=1):
                leads.append({"id": f"lead-{i:03d}", **{k: v for k, v in r.items() if k}})

    cat_ids = [c["id"] for c in cats]
    counts = [{"id": str(m.get("date", i)), "date": m.get("date", ""), "note": m.get("note", ""),
               **{c: m.get(c, 0) for c in cat_ids}} for i, m in enumerate(funnel.get("member_count", []))]
    links = [{"id": f"dest-{k}", "name": k, "type": d.get("type", ""), "url": d.get("url", "")}
             for k, d in funnel.get("destination", {}).items()]
    if br.get("control_center_url"):
        links.append({"id": "control-center", "name": "control_center", "type": "artifact", "url": br["control_center_url"]})

    summary = {"id": "summary", "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "brand_name": br.get("brand_name", ""), "ui_language": br.get("ui_language", "en"),
               "categories": [{"id": c["id"], "label": c.get("label", c["id"])} for c in cats],
               "kpis": {"groups_active": sum(1 for g in groups if g["state"] == "active"),
                        "conversations_open": sum(1 for v in convs if v["stage"] != "X"),
                        "items_posted": len(posts), "leads": len(leads)}}

    collections = {"summary": [summary], "groups": groups, "runs": runs, "scans": scans, "rejected": rejected,
                   "conversations": convs, "queue": queue_items(run_dirs), "funnel": funnel_rows, "posts": posts, "health": health(),
                   "incidents": incidents(), "readiness": readiness(caps, funnel, chans, knowledge, br, cats),
                   "knowledge": knowledge, "memberCounts": counts, "links": links, "leads": leads}

    out = ROOT / "status"
    out.mkdir(exist_ok=True)
    for name, docs in collections.items():
        (out / f"{name}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "index.json").write_text(json.dumps(
        {"generated_at": summary["generated_at"], "collections": {k: len(v) for k, v in collections.items()}},
        indent=1), encoding="utf-8")
    print(f"wrote {len(collections)} collections to {out}: " +
          ", ".join(f"{k}={len(v)}" for k, v in collections.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
