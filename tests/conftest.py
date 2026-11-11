import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "social-seeding" / "scripts"
sys.path.insert(0, str(REPO / "tools"))
import make_demo  # noqa: E402


@pytest.fixture()
def ws(tmp_path):
    """A fresh Demo Co workspace in a temp folder."""
    make_demo.main(str(tmp_path / "ws"))
    return tmp_path / "ws"


def run(ws: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "SSK_WORKSPACE": str(ws), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True,
                          encoding="utf-8", env=env, cwd=ws)
