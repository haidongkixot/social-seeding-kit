"""Helpers for /seeding-setup. Stdlib only (the prerequisite check reports what is missing).

Usage:
  python setup_workspace.py prereqs
      Check Python, openpyxl, Pillow, git, tzdata and a Chrome/Edge browser. Prints JSON; exit 1 if something required is missing.
  python setup_workspace.py init <dir> [--brand NAME] [--rep NAME] [--language en|vi|es] [--audience-tz TZ] [--operator-tz TZ]
                                      [--owner-email EMAIL] [--lang-codes en,vi,es-419] [--category id=Label ...]
      Create a workspace from the plugin's templates, write the answers into config/, copy the playbooks and the
      style guides of the chosen languages, and make a git repo (runs/, conversations/, leads and reports are git-ignored).
  python setup_workspace.py schedule [--workspace DIR]
      Show the daily run, afternoon pass and reply-check times from config/caps.toml [schedule] as cron expressions
      in the operator's timezone, and what they mean in the audience's timezone.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN / "templates"
STYLE_FILE = {"en": "en.md", "vi": "vi.md", "es-419": "es-419.md"}


# ---------------------------------------------------------------- prereqs
def prereqs() -> dict:
    out = {"python": {"ok": sys.version_info >= (3, 11), "version": sys.version.split()[0], "needs": ">= 3.11"}}
    for mod, pip in (("openpyxl", "openpyxl"), ("PIL", "Pillow")):
        out[pip] = {"ok": importlib.util.find_spec(mod) is not None, "install": f"pip install {pip}"}
    out["git"] = {"ok": shutil.which("git") is not None}
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo("Europe/Madrid")
        out["timezones"] = {"ok": True}
    except Exception:
        out["timezones"] = {"ok": False, "install": "pip install tzdata", "note": "needed to convert run times between timezones"}
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import build_queue_xlsx
        out["browser"] = {"ok": True, "path": build_queue_xlsx.find_browser()}
    except SystemExit as e:
        out["browser"] = {"ok": False, "note": str(e)}
    except ImportError as e:
        out["browser"] = {"ok": False, "note": f"{e} (install openpyxl and Pillow first)"}
    out["manual"] = ["Claude in Chrome connected to the browser where you are signed in to Facebook (you sign in, Claude never does)",
                     "Optional: Gmail connector (Facebook notification emails) and Google Drive connector"]
    return out


# ---------------------------------------------------------------- init
NL = chr(10)
EN_DEFAULTS = {"demand": ["looking for", "need a supplier", "who sells", "wholesale"],
               "qualified": ["price", "how much", "minimum", "payment", "delivery", "contact", "interested"],
               "negative": ["spam", "not interested", "stop", "report", "scam", "admin"]}


def write_keywords(path: Path, cat_ids: list[str], codes: list[str]) -> None:
    """Fresh keywords.toml: every language and category present, English phrases prefilled, the rest for the owner to fill."""
    def block(name: str, defaults: list[str]) -> str:
        rows = "".join(f"{json.dumps(c)} = {json.dumps(defaults if c == 'en' else [], ensure_ascii=False)}" + NL for c in codes)
        return f"[{name}]" + NL + rows + NL
    text = "# Search terms (scout) and intent signals (conversation-manager), by language code." + NL + NL
    text += block("demand", EN_DEFAULTS["demand"])
    text += "".join(block(f"category.{c}", []) for c in cat_ids)
    text += block("signals.qualified", EN_DEFAULTS["qualified"]) + block("signals.negative", EN_DEFAULTS["negative"]) + block("cities", [])
    path.write_text(text, encoding="utf-8")


def toml_replace(text: str, key: str, value: str) -> str:
    return re.sub(rf'^{key} = ".*"', f'{key} = {json.dumps(value, ensure_ascii=False)}', text, count=1, flags=re.M)


def init(args: argparse.Namespace) -> int:
    dest = Path(args.dir).resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"{dest} is not empty; choose a new or empty folder", file=sys.stderr)
        return 1
    shutil.copytree(TEMPLATES / "workspace", dest, dirs_exist_ok=True)
    cfg = dest / "config"
    brand = (cfg / "brand.toml").read_text(encoding="utf-8")
    for key, val in (("brand_name", args.brand), ("rep_name", args.rep), ("ui_language", args.language),
                     ("audience_timezone", args.audience_tz), ("operator_timezone", args.operator_tz),
                     ("owner_email", args.owner_email)):
        if val:
            brand = toml_replace(brand, key, val)
    (cfg / "brand.toml").write_text(brand, encoding="utf-8")

    cats = [c.split("=", 1) for c in args.category] if args.category else []
    if cats:
        catalog = "\n".join(f'[[category]]\nid = "{i}"\nlabel = {json.dumps(l, ensure_ascii=False)}\nkeywords = []\n' for i, l in cats)
        (cfg / "catalog.toml").write_text("# What you sell, as categories.\n\n" + catalog, encoding="utf-8")
        funnel = "\n".join(f'[destination.{i}]\ntype = "website"\nname = {json.dumps(l, ensure_ascii=False)}\nurl = "https://example.com/"\ncovers = []\ntracked_base = ""\n' for i, l in cats)
        counts = "".join(f"{i} = 0\n" for i, _ in cats)
        (cfg / "funnel.toml").write_text("# End of the funnel: one destination per category.\n\n" + funnel +
                                         f'\n[[member_count]]\ndate = "{dt.date.today().isoformat()}"\n{counts}note = "baseline - enter the real count"\n', encoding="utf-8")
    codes = [c.strip() for c in args.lang_codes.split(",") if c.strip()]
    if codes:
        caps = (cfg / "caps.toml").read_text(encoding="utf-8")
        head = caps.split("[languages]")[0]
        langs = "[languages]\n# native_review_done must be true before the language is used live.\n" + "".join(
            f'"{c}" = {{ native_review_done = false, reviewer = "" }}\n' for c in codes)
        (cfg / "caps.toml").write_text(head + langs, encoding="utf-8")
    if cats or codes:
        write_keywords(cfg / "keywords.toml", [i for i, _ in cats] or ["products"], codes or ["en"])
    pb = dest / "playbooks"
    for f in (TEMPLATES / "playbooks").glob("*.md"):
        shutil.copy(f, pb / f.name)
    for code in codes:
        src = STYLE_FILE.get(code) or STYLE_FILE.get(code.split("-")[0])
        if src:
            shutil.copy(TEMPLATES / "styles" / src, pb / f"{code}-style.md")
    (pb / ".gitkeep").unlink(missing_ok=True)

    if shutil.which("git"):
        run = lambda *a: subprocess.run(["git", *a], cwd=dest, capture_output=True, text=True)
        run("init", "-q")
        run("add", "-A")
        run("-c", "user.name=Seeding Setup", "-c", "user.email=setup@localhost", "commit", "-q", "-m", "Initial workspace")
    print(f"workspace created: {dest}")
    return 0


# ---------------------------------------------------------------- schedule
def to_cron(hhmm: str, tz_from: str, tz_to: str, today: dt.date | None = None) -> tuple[str, str]:
    """('M H * * *' in tz_to, 'HH:MM' in tz_to) for a wall-clock time given in tz_from. Uses today's UTC offsets."""
    from zoneinfo import ZoneInfo
    day = today or dt.date.today()
    h, m = map(int, hhmm.split(":"))
    moment = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=ZoneInfo(tz_from)).astimezone(ZoneInfo(tz_to))
    return f"{moment.minute} {moment.hour} * * *", moment.strftime("%H:%M")


def schedule(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import os
    if args.workspace:
        os.environ["SSK_WORKSPACE"] = str(Path(args.workspace).resolve())
    import common
    brand = common.brand()
    sched = common.load_toml("caps.toml").get("schedule", {})
    op, aud = brand.get("operator_timezone", "UTC"), brand.get("audience_timezone", "UTC")
    rows = []
    try:
        for name in ("daily_run", "hot_replies"):
            if sched.get(name):
                cron, _ = to_cron(sched[name], op, op)
                _, aud_time = to_cron(sched[name], op, aud)
                rows.append({"job": name, "cron_operator_tz": cron, "operator_time": sched[name], "audience_time": aud_time})
        hours = sched.get("check_replies_hours", "")
        if hours:
            a, b = hours.split("-")
            _, a_aud = to_cron(a, op, aud)
            _, b_aud = to_cron(b, op, aud)
            rows.append({"job": "check_replies", "cron_operator_tz": f"7 {int(a[:2])}-23,0-{int(b[:2])} * * *" if int(a[:2]) > int(b[:2]) else f"7 {int(a[:2])}-{int(b[:2])} * * *",
                         "operator_time": hours, "audience_time": f"{a_aud}-{b_aud}"})
    except Exception as e:   # missing tzdata or a bad zone name
        print(f"cannot convert timezones ({type(e).__name__}: {e}); run: pip install tzdata", file=sys.stderr)
        return 1
    print(json.dumps({"operator_timezone": op, "audience_timezone": aud, "jobs": rows}, ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prereqs")
    i = sub.add_parser("init")
    i.add_argument("dir")
    i.add_argument("--brand"), i.add_argument("--rep"), i.add_argument("--language", choices=["en", "vi", "es"])
    i.add_argument("--audience-tz"), i.add_argument("--operator-tz"), i.add_argument("--owner-email")
    i.add_argument("--lang-codes", default="")
    i.add_argument("--category", action="append", default=[], help="id=Label, repeatable")
    s = sub.add_parser("schedule")
    s.add_argument("--workspace")
    args = ap.parse_args()
    if args.cmd == "prereqs":
        r = prereqs()
        print(json.dumps(r, indent=1))
        return 0 if all(v.get("ok", True) for k, v in r.items() if isinstance(v, dict)) else 1
    return {"init": init, "schedule": schedule}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
