"""Render the control-center page locally with a stubbed artifact runtime (no network to claude.ai).

Usage:
  python tools/render_page.py shots <out_dir> [--lang en|vi|es] [--readonly]     screenshots of every tab (1280 and 400 wide)
  python tools/render_page.py dom   <script.js> [--lang en] [--readonly]          run a script in the page, print its result

Fixture data comes from the demo workspace (status/*.json from build_status.py and the config documents
from config_sync.py export), plus sample approval marks, control state and notes.
Needs Chrome or Edge (SSK_BROWSER overrides the path).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "social-seeding"
SCRIPTS = PLUGIN / "scripts"
STUB = REPO / "tests" / "stub" / "claude_stub.js"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "tools"))


def find_browser() -> str:
    import build_queue_xlsx
    return build_queue_xlsx.find_browser()


def fixture(workspace: Path) -> dict[str, list[dict]]:
    """Collections for the stub db, built from a workspace (runs build_status and config_sync export)."""
    env = {**os.environ, "SSK_WORKSPACE": str(workspace), "PYTHONIOENCODING": "utf-8"}
    for script, args in (("build_status.py", []), ("config_sync.py", ["export"])):
        subprocess.run([sys.executable, str(SCRIPTS / script), *args], check=True, capture_output=True, env=env, cwd=workspace)
    fx: dict[str, list[dict]] = {}
    for f in (workspace / "status").glob("*.json"):
        if f.name not in ("index.json", "sync-report.json"):
            fx[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    fx["config"] = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((workspace / "status" / "config").glob("*.json"))]
    latest = max((i["date"] for i in fx.get("queue", [])), default="")
    q = [i for i in fx.get("queue", []) if i["date"] == latest]
    fx["approvals"] = [{"id": q[0]["id"], "queue_id": q[0]["id"], "decision": "approve", "note": ""},
                       {"id": q[1]["id"], "queue_id": q[1]["id"], "decision": "edit", "note": "Make it shorter"}] if len(q) > 1 else []
    fx["control"] = [{"id": "state", "paused": False, "pausedChannels": []},
                     {"id": "syncResult", "ok": True, "at": "2026-11-12T08:01:00Z", "changed": ["config/brand.toml"], "errors": []}]
    fx["runRequests"] = [{"id": "r-1", "kind": "daily-run", "status": "pending", "requestedAt": "2026-11-12T07:55:00Z"}]
    fx["notes"] = [{"id": "n-1", "text": "Prefer shorter replies on the board.", "status": "handled", "createdAt": "2026-11-11T10:00:00Z"}]
    return fx


def page_html(fx: dict, lang: str, readonly: bool, script: str = "") -> str:
    html = (PLUGIN / "page" / "control-center.html").read_text(encoding="utf-8")
    head = ("<script>window.__ERRS=[];window.addEventListener('error',function(e){window.__ERRS.push(e.message+' @'+e.lineno)});"
            "window.addEventListener('unhandledrejection',function(e){window.__ERRS.push('rejection: '+(e.reason&&e.reason.message||e.reason))});</script>"
            "<script>window.__SSK_FIXTURE=" + json.dumps(fx, ensure_ascii=False).replace("</", "<\\/") + ";"
            + f"window.__SSK_LANG={json.dumps(lang)};window.__SSK_READONLY={str(readonly).lower()};</script>"
            + "<script>" + STUB.read_text(encoding="utf-8") + "</script>")
    html = html.replace('<div class="wrap" id="app"></div>', '<div class="wrap" id="app"></div>' + head, 1)
    if script:
        html = html.replace("boot();\n</script>", "boot();\n</script><script>" + script + "</script>")
    return html


def run_browser(args: list[str], html_path: Path) -> subprocess.CompletedProcess:
    profile = tempfile.mkdtemp(prefix="ssk-edge-")
    try:
        return subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                               *args, html_path.resolve().as_uri()], capture_output=True, text=True, encoding="utf-8", timeout=120)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def shots(out: Path, lang: str, readonly: bool, workspace: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    fx = fixture(workspace)
    page = out / f"page-{lang}.html"
    page.write_text(page_html(fx, lang, readonly), encoding="utf-8")
    made = []
    for tab in ("setup", "channels", "approvals", "dashboard", "control"):
        for name, size in (("wide", "1280,1500"), ("phone", "400,1400")):
            png = out / f"{tab}-{lang}-{name}.png"
            html = out / f"_{tab}.html"
            html.write_text(page.read_text(encoding="utf-8").replace("boot();\n</script>", f"location.hash='{tab}';boot();\n</script>", 1), encoding="utf-8")
            run_browser([f"--screenshot={png.resolve()}", f"--window-size={size}", "--virtual-time-budget=4000"], html)
            html.unlink()
            if png.exists():
                made.append(png)
    return made


def dom(script_path: Path, lang: str, readonly: bool, workspace: Path) -> str:
    """Run a test script after boot; it should put its result in element #__result."""
    fx = fixture(workspace)
    tmp = Path(tempfile.mkdtemp(prefix="ssk-dom-"))
    page = tmp / "page.html"
    page.write_text(page_html(fx, lang, readonly, script_path.read_text(encoding="utf-8")), encoding="utf-8")
    try:
        r = run_browser(["--dump-dom", "--virtual-time-budget=15000"], page)
        return r.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1]
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "en"
    ro = "--readonly" in sys.argv
    ws = REPO / "demo"
    if mode == "shots":
        for p in shots(Path(sys.argv[2]), lang, ro, ws):
            print(p)
    else:
        print(dom(Path(sys.argv[2]), lang, ro, ws))
