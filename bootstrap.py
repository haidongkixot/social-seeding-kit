"""One command from a fresh clone to the control center's Setup page.

Usage (from the cloned repo):
  Windows:      setup.cmd                  (or: python bootstrap.py)
  macOS/Linux:  ./setup.sh                 (or: python3 bootstrap.py)

Options:
  --brand NAME        brand name (asked if missing; the workspace folder is named after it)
  --workspace PATH    workspace folder (default: <folder above this repo>/<brand>-seeding)
  --language en|vi|es interface language (default: vi)
  --no-launch         prepare everything but do not start Claude Code
  --skip-pip          do not install Python packages
  --skip-claude       do not register the plugin with Claude Code (for tests)

Steps: install Python packages, create the workspace, register this repo as a Claude Code marketplace,
install the plugin for that workspace only, then start Claude Code there with /social-seeding:seeding-setup,
which publishes the control center and sends you to its Setup tab.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent
SETUP = REPO / "plugins" / "social-seeding" / "scripts" / "setup_workspace.py"
PACKAGES = ["openpyxl", "Pillow", "tzdata"]
MARKETPLACE = "social-seeding-kit"
PLUGIN = "social-seeding@social-seeding-kit"


def say(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def slug(text: str) -> str:
    t = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "brand"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if check and r.returncode != 0:
        print((r.stdout or "") + (r.stderr or ""), file=sys.stderr)
        raise SystemExit(f"failed: {' '.join(cmd)}")
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand")
    ap.add_argument("--workspace")
    ap.add_argument("--language", choices=["en", "vi", "es"], default="vi")
    ap.add_argument("--no-launch", action="store_true")
    ap.add_argument("--skip-pip", action="store_true")
    ap.add_argument("--skip-claude", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is needed: https://www.python.org/downloads/")

    # 1. Python packages
    if not a.skip_pip:
        say("Installing Python packages: " + ", ".join(PACKAGES))
        run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *PACKAGES])

    # 2. Workspace
    brand = a.brand
    if not brand and not a.workspace:
        brand = input("Brand name / Tên thương hiệu: ").strip() or "My Brand"
    ws = Path(a.workspace).expanduser().resolve() if a.workspace else REPO.parent / f"{slug(brand)}-seeding"
    if (ws / "config" / "brand.toml").exists():
        say(f"Workspace already exists, reusing it: {ws}")
    else:
        say(f"Creating the workspace: {ws}")
        cmd = [sys.executable, str(SETUP), "init", str(ws), "--language", a.language]
        if brand:
            cmd += ["--brand", brand]
        r = run(cmd, check=False)
        if r.returncode != 0:
            raise SystemExit(r.stderr.strip() or r.stdout.strip())

    # 3. Plugin, registered with Claude Code for this workspace only
    if not a.skip_claude:
        claude = shutil.which("claude")
        if not claude:
            raise SystemExit("Claude Code is not installed. Install it from https://claude.com/claude-code, then run this again.")
        known = run([claude, "plugin", "marketplace", "list"], check=False).stdout
        if MARKETPLACE in known:
            say("Updating the marketplace from this repo")
            run([claude, "plugin", "marketplace", "update", MARKETPLACE], check=False)
        else:
            say("Registering this repo as a Claude Code marketplace")
            run([claude, "plugin", "marketplace", "add", str(REPO)])
        say("Installing the plugin for this workspace only")
        r = run([claude, "plugin", "install", PLUGIN, "--scope", "local"], cwd=ws, check=False)
        if r.returncode != 0 and "already" not in (r.stdout + r.stderr).lower():
            print(r.stdout + r.stderr, file=sys.stderr)
            raise SystemExit("plugin install failed")

    # 4. Start
    say("Ready. / Sẵn sàng.")
    if a.no_launch or a.skip_claude:
        print(f'\nNext: cd "{ws}"  and run:  claude "/social-seeding:seeding-setup"')
        return 0
    say("Starting Claude Code: it publishes the control center and opens the Setup tab")
    return subprocess.call([shutil.which("claude"), "/social-seeding:seeding-setup"], cwd=ws)


if __name__ == "__main__":
    sys.exit(main())
