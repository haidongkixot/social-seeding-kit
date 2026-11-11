"""Funnel and activity numbers for the reporter. Prints JSON.

Usage: python scripts/funnel_stats.py --since 2026-11-11 [--until 2026-11-24]

Conversations count if their 'opened' date is in the period. A conversation's funnel depth is its
max_stage (kept even after it is CLOSED). Posted items come from runs/<date>/post-log*.csv.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, category_ids, channels, front_matter, load_toml  # noqa: E402

STAGE_NAMES = ["seeded", "engaged", "qualified", "invited", "joined"]


def in_period(d: str, since: dt.date, until: dt.date) -> bool:
    try:
        return since <= dt.date.fromisoformat(d[:10]) <= until
    except ValueError:
        return False


def funnel(rows: list[dict]) -> dict:
    depth = Counter()
    for r in rows:
        depth[r["max_stage"]] += 1
    reached = {name: sum(v for k, v in depth.items() if k >= i) for i, name in enumerate(STAGE_NAMES)}
    conv = {}
    for a, b in zip(STAGE_NAMES, STAGE_NAMES[1:]):
        conv[f"{a}->{b}"] = round(reached[b] / reached[a], 3) if reached[a] else None
    return {"reached": reached, "conversion": conv, "closed": sum(1 for r in rows if r["stage"] == "X")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--until", default=dt.date.today().isoformat())
    a = ap.parse_args()
    since, until = dt.date.fromisoformat(a.since), dt.date.fromisoformat(a.until)
    chans = channels()

    rows = []
    for p in sorted((ROOT / "conversations").glob("*.md")) if (ROOT / "conversations").exists() else []:
        fm, _ = front_matter(p)
        if not in_period(fm.get("opened", ""), since, until):
            continue
        try:
            ms = int(fm.get("max_stage", "0"))
        except ValueError:
            ms = 0
        ch = chans.get(fm.get("channel", ""), {})
        rows.append({
            "id": fm.get("id"), "channel": fm.get("channel"), "playbook": fm.get("playbook"),
            "category": fm.get("category"), "identity": fm.get("identity"),
            "language": ch.get("language", "?"), "kind": ch.get("kind", "?"),
            "stage": fm.get("stage"), "max_stage": ms, "closed_reason": fm.get("closed_reason", ""),
        })

    by = {}
    for dim in ("channel", "playbook", "category", "identity", "language", "kind"):
        groups = defaultdict(list)
        for r in rows:
            groups[r[dim]].append(r)
        by[dim] = {k: funnel(v) for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}

    posted = Counter()
    posted_by_channel = Counter()
    status = Counter()
    links = 0
    for log in sorted((ROOT / "runs").glob("*/post-log*.csv")) if (ROOT / "runs").exists() else []:
        with open(log, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if not in_period(r.get("datetime", ""), since, until):
                    continue
                status[r.get("status", "?")] += 1
                if r.get("status") in {"posted", "pending"}:
                    posted[r.get("type", "?")] += 1
                    posted_by_channel[r.get("channel", "?")] += 1
                    links += r.get("has_link", "").lower() in {"true", "1", "yes"}

    engaged_by_channel = Counter(r["channel"] for r in rows if r["max_stage"] >= 1)
    invited_by_channel = Counter(r["channel"] for r in rows if r["max_stage"] >= 3)
    channel_rank = sorted(
        ({"channel": c, "name": chans.get(c, {}).get("name", ""), "items": n,
          "engaged": engaged_by_channel[c], "invited": invited_by_channel[c],
          "engaged_per_item": round(engaged_by_channel[c] / n, 3)} for c, n in posted_by_channel.items()),
        key=lambda x: (-x["engaged_per_item"], -x["items"]))

    cats = category_ids()
    wa = load_toml("funnel.toml").get("member_count", [])
    wa_period = [m for m in wa if in_period(str(m.get("date", "")), since - dt.timedelta(days=3), until)]
    joins = None
    if len(wa_period) >= 2:
        first, last = wa_period[0], wa_period[-1]
        joins = {k: last.get(k, 0) - first.get(k, 0) for k in cats}

    out = {
        "period": {"since": a.since, "until": a.until},
        "conversations": len(rows),
        "funnel": funnel(rows),
        "by": by,
        "items_posted_by_type": dict(posted),
        "items_by_status": dict(status),
        "items_with_links": links,
        "channel_rank": channel_rank,
        "destination_joins": joins if joins is not None else "n/a (need 2+ member counts in period)",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
