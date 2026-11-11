"""Build queue.md and review.html from a run's queue.json.

Usage: python scripts/build_review.py runs/2026-11-11 [--suffix -pm]

queue.json is either a list of items or {"health": {...}, "items": [...]}.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, channels  # noqa: E402

STAGE = {0: "SEED", 1: "ENGAGED", 2: "QUALIFIED", 3: "INVITED", 4: "JOINED"}
TYPE_LABEL = {"comment": "New seed", "reply": "Reply", "offer_post": "Offer post",
              "invite": "Invite", "dm_invite": "DM invite", "dm": "DM"}

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--mute:#6b6b66;--line:#e3e2dc;--accent:#1f3a8a;
--ok:#1a7f37;--warn:#9a6700;--bad:#cf222e;--chip:#eef0f6}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--mute:#a3a29b;
--line:#33332f;--accent:#8fa8ff;--ok:#4ac26b;--warn:#d4a72c;--bad:#ff7b72;--chip:#262a36}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mute);margin:0 0 16px}
.banner{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:0 0 16px;background:var(--card)}
.banner.draft{border-color:var(--warn)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:0 0 12px}
.head{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.n{font-weight:700;font-size:18px;margin-right:4px}
.chip{background:var(--chip);border-radius:999px;padding:2px 9px;font-size:12.5px}
.ctx{color:var(--mute);font-size:13.5px;margin:0 0 8px}
.text{white-space:pre-wrap;border-left:3px solid var(--accent);padding:6px 10px;margin:0 0 8px;font-size:15.5px}
.meta{font-size:12.5px;color:var(--mute)}.meta b{color:var(--ink);font-weight:600}
.PASS{color:var(--ok)}.FIX{color:var(--warn)}.DROP,.CUT{color:var(--bad)}
a{color:var(--accent);word-break:break-all}
.how{font-size:13.5px;color:var(--mute);margin-top:20px}
"""


def load_items(run: Path, suffix: str) -> tuple[dict, list[dict]]:
    data = json.loads((run / f"queue{suffix}.json").read_text(encoding="utf-8-sig"))  # tolerate a BOM (PowerShell 5.1 writes one)
    if isinstance(data, list):
        return {}, data
    return data.get("health", {}), data.get("items", [])


def stage_txt(item: dict) -> str:
    a, b = item.get("stage_from"), item.get("stage_to")
    if a is None:
        return ""
    sa, sb = STAGE.get(a, str(a)), STAGE.get(b, str(b))
    return sa if sa == sb else f"{sa} → {sb}"


def to_md(run: Path, health: dict, items: list[dict], chans: dict) -> str:
    lines = [f"# Queue {run.name}", ""]
    if health:
        lines.append("Health: " + ", ".join(f"{k} {v}" for k, v in health.items()))
        lines.append("")
    for it in items:
        ch = chans.get(it.get("channel"), {})
        lines += [
            f"## {it['n']}. {TYPE_LABEL.get(it.get('type'), it.get('type'))} · {it.get('channel')} {ch.get('name', '')}",
            f"- stage: {stage_txt(it)} · identity: {it.get('identity')} · lang: {it.get('language')} · category: {it.get('category')}",
            f"- target: {it.get('target_url', '')}",
            f"- thread: {it.get('thread_summary', '')}",
            f"- why: {it.get('why', '')}",
            f"- review: {it.get('review', {}).get('verdict', '?')} · risk: {it.get('risk', {}).get('verdict', '?')}"
            + (" · DRAFT ONLY" if it.get("draft_only") else ""),
            "",
            "> " + it.get("text", "").replace("\n", "\n> "),
            "",
        ]
    lines.append("Reply in chat: `approve 1-5, 8; edit 3: <new text>; drop 6`")
    return "\n".join(lines) + "\n"


def to_html(run: Path, health: dict, items: list[dict], chans: dict) -> str:
    e = html.escape
    draft = any(it.get("draft_only") for it in items)
    counts: dict[str, int] = {}
    for it in items:
        counts[it.get("type", "?")] = counts.get(it.get("type", "?"), 0) + 1
    summary = " · ".join(f"{v} {TYPE_LABEL.get(k, k).lower()}" for k, v in counts.items()) or "no items"
    out = [
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Seeding queue {e(run.name)}</title><style>{CSS}</style></head><body><main>",
        f"<h1>Seeding queue — {e(run.name)}</h1><p class='sub'>{len(items)} items: {e(summary)}</p>",
    ]
    if health:
        out.append("<div class='banner'>Health: " + " · ".join(
            f"<b>{e(str(k))}</b> <span class='{e(str(v))}'>{e(str(v))}</span>" for k, v in health.items()) + "</div>")
    if draft:
        out.append("<div class='banner draft'><b>Draft only.</b> Uses DRAFT knowledge and/or a language "
                   "without native review. These items cannot be posted yet.</div>")
    for it in items:
        ch = chans.get(it.get("channel"), {})
        rv, rk = it.get("review", {}), it.get("risk", {})
        link = it.get("target_url", "")
        out.append("<section class='card'>")
        out.append(
            f"<div class='head'><span class='n'>{e(str(it.get('n')))}</span>"
            f"<span class='chip'>{e(TYPE_LABEL.get(it.get('type'), str(it.get('type'))))}</span>"
            f"<span class='chip'>{e(str(it.get('channel')))} · {e(ch.get('name', ''))}</span>"
            + (f"<span class='chip'>{e(stage_txt(it))}</span>" if stage_txt(it) else "")
            + f"<span class='chip'>{e(str(it.get('category', '')))}</span>"
            f"<span class='chip'>as {e(str(it.get('identity', '')))}</span></div>"
        )
        if it.get("thread_summary"):
            out.append(f"<p class='ctx'>{e(it['thread_summary'])}</p>")
        out.append(f"<div class='text'>{e(it.get('text', ''))}</div>")
        out.append("<div class='meta'>")
        if link:
            out.append(f"<div><b>Where:</b> <a href='{e(link)}' target='_blank' rel='noopener'>{e(link)}</a></div>")
        if it.get("why"):
            out.append(f"<div><b>Why:</b> {e(it['why'])}</div>")
        if it.get("facts"):
            out.append(f"<div><b>Facts:</b> {e(', '.join(it['facts']))}</div>")
        out.append(
            f"<div><b>Review:</b> <span class='{e(rv.get('verdict', ''))}'>{e(rv.get('verdict', '?'))}</span>"
            + (f" — {e(rv.get('notes', ''))}" if rv.get("notes") else "")
            + f" · <b>Risk:</b> <span class='{e(rk.get('verdict', ''))}'>{e(rk.get('verdict', '?'))}</span>"
            + (f" — {e(rk.get('notes', ''))}" if rk.get("notes") else "")
            + "</div>"
        )
        out.append("</div></section>")
    out.append("<p class='how'>Approve in the Claude chat, e.g. <code>approve 1-5, 8; edit 3: new text; drop 6</code>. "
               "Nothing is posted until you do.</p></main></body></html>")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="run folder, e.g. runs/2026-11-11")
    ap.add_argument("--suffix", default="", help="e.g. -pm for the afternoon queue")
    a = ap.parse_args()
    run = Path(a.run)
    if not run.is_absolute():
        run = ROOT / run
    health, items = load_items(run, a.suffix)
    chans = channels()
    (run / f"queue{a.suffix}.md").write_text(to_md(run, health, items, chans), encoding="utf-8")
    (run / f"review{a.suffix}.html").write_text(to_html(run, health, items, chans), encoding="utf-8")
    print(f"wrote {run / f'queue{a.suffix}.md'} and {run / f'review{a.suffix}.html'} ({len(items)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
