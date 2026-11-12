import subprocess
import sys
import tomllib

from conftest import REPO, run


def bootstrap(*args):
    return subprocess.run([sys.executable, str(REPO / "bootstrap.py"), "--skip-pip", "--skip-claude", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_bootstrap_creates_a_ready_workspace(tmp_path):
    ws = tmp_path / "acme-seeding"
    r = bootstrap("--brand", "Công ty Acme", "--workspace", str(ws))
    assert r.returncode == 0, r.stderr
    assert "seeding-setup" in r.stdout
    brand = tomllib.loads((ws / "config/brand.toml").read_text(encoding="utf-8"))["brand"]
    assert brand["brand_name"] == "Công ty Acme" and brand["ui_language"] == "vi"
    assert run(ws, "validate.py").returncode == 0


def test_bootstrap_reuses_an_existing_workspace(tmp_path):
    ws = tmp_path / "ws"
    assert bootstrap("--brand", "A", "--workspace", str(ws)).returncode == 0
    (ws / "config" / "brand.toml").write_text((ws / "config" / "brand.toml").read_text(encoding="utf-8").replace('"A"', '"Kept"'), encoding="utf-8")
    r = bootstrap("--brand", "B", "--workspace", str(ws))
    assert r.returncode == 0 and "reusing" in r.stdout
    assert '"Kept"' in (ws / "config" / "brand.toml").read_text(encoding="utf-8")


def test_default_workspace_name_comes_from_the_brand():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bootstrap", REPO / "bootstrap.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.slug("Công ty Đại Phát") == "cong-ty-dai-phat"
