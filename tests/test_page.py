import html
import json
import re
import sys
import tempfile
import tomllib
from pathlib import Path

import pytest
from conftest import REPO, run

sys.path.insert(0, str(REPO / "tools"))
import build_page  # noqa: E402
import render_page  # noqa: E402

SCENARIOS = (REPO / "tests" / "page_scenarios.js").read_text(encoding="utf-8")

try:
    render_page.find_browser()
    HAVE_BROWSER = True
except SystemExit:
    HAVE_BROWSER = False
needs_browser = pytest.mark.skipif(not HAVE_BROWSER, reason="no Chrome or Edge found")


def scenario(ws, name, lang="en", readonly=False):
    script = Path(tempfile.mkdtemp()) / "s.js"
    script.write_text(f'const SCENARIO = "{name}";\n' + SCENARIOS, encoding="utf-8")
    dom = render_page.dom(script, lang, readonly, ws)
    m = re.search(r'<pre id="__result">(.*?)</pre>', dom, re.S)
    assert m, "no result from the page (script error?)"
    out = json.loads(html.unescape(m.group(1)))
    assert not out.get("errs"), out["errs"]
    assert "error" not in out, out["error"]
    return out


# ---------------------------------------------------------------- static checks (no browser)
def test_built_page_is_current_and_i18n_complete():
    problems = build_page.problems(build_page.SRC.read_text(encoding="utf-8"), build_page.load())
    assert not problems, problems
    assert build_page.OUT.read_text(encoding="utf-8") == build_page.build(), "run python tools/build_page.py"


def test_i18n_languages_are_translated():
    i18n = build_page.load()
    same = [k for k, v in i18n["en"].items() if not k.startswith("_") and (v == i18n["vi"][k] or v == i18n["es"][k])
            and len(v) > 12]
    assert not same, same      # long strings identical to English were left untranslated


def test_page_has_no_external_scripts_and_is_theme_aware():
    page = build_page.OUT.read_text(encoding="utf-8")
    assert not re.findall(r"<script[^>]+src=", page)
    assert "prefers-color-scheme: dark" in page and 'data-theme="dark"' in page
    assert "innerHTML" not in build_page.SRC.read_text(encoding="utf-8")   # shared data is never parsed as HTML
    assert "fonts.googleapis.com" in page and "claude:viewport-fit-sides" in page


# ---------------------------------------------------------------- browser scenarios
@needs_browser
def test_page_boots_with_five_tabs(ws):
    out = scenario(ws, "boot")["result"]
    assert out["tabs"][0] == "Setup" and len(out["tabs"]) == 5 and out["brand"] == "Demo Co" and not out["readonly"]


@needs_browser
@pytest.mark.parametrize("lang,word", [("vi", "Thiết lập"), ("es", "Configuración")])
def test_page_renders_in_other_languages(ws, lang, word):
    out = scenario(ws, "boot", lang=lang)["result"]
    assert out["tabs"][0] == word


@needs_browser
def test_approvals_marks_are_saved_as_proposals(ws):
    out = scenario(ws, "approvals")["result"]
    assert out["cards"] == 4 and out["phrase"]
    assert out["ids"][0].startswith("set approvals/") and out["afterToggle"][-1] == "delete"
    assert out["editWrite"]["decision"] == "edit" and out["editWrite"]["note"] == "Say it shorter"


@needs_browser
def test_setup_brand_save_writes_one_config_document(ws):
    r = scenario(ws, "setup_brand")
    out = r["result"]
    assert out["flagVisible"] and out["write"]["brand_name"] == "Acme Seeds" and out["write"]["_updated"]
    assert [w["path"] for w in r["writes"]] == ["config/brand"]


@needs_browser
def test_setup_invalid_timezone_blocks_save(ws):
    out = scenario(ws, "setup_invalid")["result"]
    assert out["wrote"] == 0 and any("timezone" in e for e in out["errors"])


@needs_browser
def test_channels_paste_and_save(ws):
    out = scenario(ws, "channels_add")["result"]
    assert out["rows"] == 5
    assert out["channels"][-2:] == [["C4", "discussion", "not_joined", "en", "home"], ["C5", "page", "not_joined", "en", "home"]]


@needs_browser
def test_active_channel_needs_joined_date(ws):
    out = scenario(ws, "channels_activate_needs_date")["result"]
    assert not out["wrote"] and any("date you joined" in e for e in out["errors"])


@needs_browser
def test_categories_step_reconciles_funnel_and_channels(ws):
    out = scenario(ws, "categories_add")["result"]
    assert out["catalog"] == ["home", "build", "garden-tools"]
    assert set(out["funnel"]) == {"home", "build", "garden-tools"} and out["channels"]


@needs_browser
def test_facts_step(ws):
    out = scenario(ws, "facts_add")["result"]
    assert out["write"][0]["text"] == "We ship by the pallet." and out["write"][0]["approved"] is True


@needs_browser
def test_control_tab_pause_requests_notes(ws):
    out = scenario(ws, "control")["result"]
    assert out["paused"]["paused"] is True and out["banner"]
    assert out["req"]["status"] == "pending" and out["note"]["status"] == "new" and out["note"]["text"].startswith("Please post")
    assert out["pausedChannels"] == ["A1"]


@needs_browser
def test_schedule_validation(ws):
    out = scenario(ws, "schedule_invalid")["result"]
    assert not out["wrote"] and out["errors"]


@needs_browser
def test_viewer_without_edit_access_cannot_write(ws):
    out = scenario(ws, "readonly", readonly=True)["result"]
    assert out["banner"] and out["disabled"] and out["pauseDisabled"] and out["writes"] == 0


@needs_browser
def test_dashboard_sections_render(ws):
    out = scenario(ws, "dashboard")["result"]
    assert out["Conversations"]["rows"] == 6 and out["Leads"]["rows"] == 1 and out["Posts"]["rows"] == 2
    assert out["Health"]["rows"] == 1 and out["leadContact"] == ["+00 000 000 001"]


@needs_browser
def test_markup_in_shared_data_is_shown_as_text(ws):
    out = scenario(ws, "xss")["result"]
    assert not out["pwned"] and not out["hasImg"] and out["shown"]


# ---------------------------------------------------------------- page edit -> TOML -> validate -> dashboard
@needs_browser
def test_page_writes_round_trip_through_sync_and_validate(ws):
    docs = {}
    for name in ("categories_add", "setup_brand"):
        for w in scenario(ws, name)["writes"]:
            if w["path"].startswith("config/"):
                docs[w["path"].split("/")[1]] = w["data"]
    d = ws / "status" / "pull"
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(json.dumps(list(docs.values())), encoding="utf-8")
    rep = run(ws, "control_sync.py", str(d))
    assert rep.returncode == 0, rep.stderr
    assert "config/catalog.toml" in rep.stdout
    v = run(ws, "validate.py")
    assert v.returncode == 0, v.stdout
    cats = tomllib.loads((ws / "config" / "catalog.toml").read_text(encoding="utf-8"))["category"]
    assert [c["id"] for c in cats] == ["home", "build", "garden-tools"]
    assert run(ws, "build_status.py").returncode == 0
    summary = json.loads((ws / "status" / "summary.json").read_text(encoding="utf-8"))[0]
    assert [c["id"] for c in summary["categories"]] == ["home", "build", "garden-tools"]
    assert summary["brand_name"] == "Acme Seeds"
