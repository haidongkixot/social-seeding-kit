"""Turn the control center's documents (read from its database) into workspace files and a report.

Usage: python scripts/control_sync.py <pull-dir> [--dry-run]

<pull-dir> holds one JSON list per collection, as the sync-control skill saved them from the artifact database:
  config.json        documents {id: brand|catalog|funnel|channels|caps|keywords|languages|facts, ...} -> config/*.toml
                     Only documents the owner edited on the page are applied: _updated is set and is newer than _synced.
                     The skill then writes _synced (the ids are in the report's "synced" list).
  approvals.json     {id, queue_id, decision: approve|edit|drop, note}                              -> runs/<date>/marked.json
  control.json       {id: "state", paused, pausedChannels[]}                                        -> runs/control-state.json
  runRequests.json   {id, kind, status, note}                                                       -> reported only
  notes.json         {id, text, status}                                                             -> reported only

Nothing here posts, joins or messages. Approval marks and run requests are proposals the owner must confirm
in chat; notes that ask for an outward action are flagged `needs_chat_confirmation`. The report is printed as
JSON and saved to status/sync-report.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config_sync  # noqa: E402
from common import ROOT  # noqa: E402

DECISIONS = {"approve", "edit", "drop"}
KINDS = {"daily-run", "hot-replies", "check-replies", "health-check", "biweekly-report"}
# Words (en/vi/es) that ask for an outward action. Such a note is a request to ask the owner in chat, never an order.
ACTION = re.compile(r"\b(post|comment|reply|dm|message|join|follow|invite|send|publish|đăng|bình luận|trả lời|nhắn|"
                    r"tham gia|gửi|mời|publicar|comentar|responder|unirse|enviar|invitar|mensaje)\b", re.I)
# Words that ask to weaken the fixed safety rules.
BYPASS = re.compile(r"(ignore (the )?(rules|safety)|skip (the )?approval|without approval|no approval|bỏ qua duyệt|"
                    r"không cần duyệt|sin aprobaci|saltar la aprobaci|evade|bypass|proxy|fake (account|profile))", re.I)


def read_list(d: Path, name: str) -> list[dict]:
    p = d / f"{name}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, list) else list(data.values())


def latest_queue_ids() -> tuple[str, set[str]]:
    runs = sorted(p for p in (ROOT / "runs").glob("*") if p.is_dir()) if (ROOT / "runs").exists() else []
    for d in reversed(runs):
        ids = set()
        for f in d.glob("queue*.json"):
            q = json.loads(f.read_text(encoding="utf-8-sig"))
            items = q.get("items", []) if isinstance(q, dict) else q
            tag = f.stem.removeprefix("queue")
            ids |= {f"{d.name}{tag}-{it.get('n')}" for it in items}
        if ids:
            return d.name, ids
    return "", set()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pull_dir")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    d = Path(args.pull_dir)
    report: dict = {"config_changed": [], "synced": [], "config_clean": [], "marked": [], "stale_marks": [], "requests": [], "notes": [], "paused": False,
                    "paused_channels": []}

    docs = {}
    for x in read_list(d, "config"):
        if x.get("id") not in config_sync.DOCS:
            continue
        if x.get("_updated") and str(x["_updated"]) > str(x.get("_synced", "")):
            docs[x["id"]] = x
        else:
            report["config_clean"].append(x["id"])        # unchanged on the page: the workspace files stay as they are
    report["synced"] = sorted(docs)
    if docs:
        report["config_changed"] = config_sync.apply_docs(docs, args.dry_run)

    date, valid = latest_queue_ids()
    marks = []
    for a in read_list(d, "approvals"):
        dec = str(a.get("decision", "")).lower()
        if dec not in DECISIONS:
            continue
        if a.get("queue_id") in valid:
            marks.append({"queue_id": a["queue_id"], "decision": dec, "note": a.get("note", "")})
        else:
            report["stale_marks"].append(a.get("queue_id"))
    report["marked"] = marks
    if marks and date and not args.dry_run:
        (ROOT / "runs" / date / "marked.json").write_text(json.dumps(marks, ensure_ascii=False, indent=1), encoding="utf-8")

    state = next((x for x in read_list(d, "control") if x.get("id") == "state"), {})
    report["paused"] = bool(state.get("paused", False))
    report["paused_channels"] = list(state.get("pausedChannels", []))
    if not args.dry_run and (ROOT / "runs").exists():
        (ROOT / "runs" / "control-state.json").write_text(
            json.dumps({"paused": report["paused"], "pausedChannels": report["paused_channels"]}), encoding="utf-8")

    for r in read_list(d, "runRequests"):
        if r.get("status", "pending") == "pending":
            report["requests"].append({"id": r.get("id"), "kind": r.get("kind"), "valid_kind": r.get("kind") in KINDS,
                                       "note": r.get("note", "")})
    for n in read_list(d, "notes"):
        if n.get("status", "new") != "new":
            continue
        text = str(n.get("text", ""))
        report["notes"].append({"id": n.get("id"), "text": text,
                                "needs_chat_confirmation": bool(ACTION.search(text)),
                                "conflicts_with_safety": bool(BYPASS.search(text))})

    if not args.dry_run:
        out = ROOT / "status"
        out.mkdir(exist_ok=True)
        (out / "sync-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
