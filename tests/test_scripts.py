import json
import tomllib
from pathlib import Path

from conftest import REPO, SCRIPTS, run

TEMPLATE = REPO / "plugins" / "social-seeding" / "templates" / "workspace"


def toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8")


# ---------------------------------------------------------------- validate
def test_demo_validates(ws):
    r = run(ws, "validate.py")
    assert r.returncode == 0, r.stdout
    assert "0 error(s)" in r.stdout


def test_template_validates():
    r = run(TEMPLATE, "validate.py")
    assert r.returncode == 0, r.stdout


def test_unknown_category_in_channel_fails(ws):
    edit(ws / "config" / "channels.toml", 'fit = ["home", "build"]', 'fit = ["fmcg"]')
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "fit must be" in r.stdout


def test_funnel_destination_type_and_url(ws):
    edit(ws / "config" / "funnel.toml", "https://chat.whatsapp.com/DEMOHOME0000000000000", "https://example.com/x")
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "whatsapp url must start with" in r.stdout


def test_missing_destination_fails(ws):
    edit(ws / "config" / "catalog.toml", 'id = "build"', 'id = "build"\nlabel_x = 1\n\n[[category]]\nid = "extra"\nlabel = "Extra"\nkeywords = ["x"]\n\n[[category]]\nid = "tail"')
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "missing [destination.extra]" in r.stdout


def test_fanpage_url_allowed_only_with_kind_page(ws):
    edit(ws / "config" / "channels.toml", 'kind = "page"', 'kind = "discussion"')
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "must contain /groups/" in r.stdout


def test_language_must_be_declared(ws):
    edit(ws / "config" / "channels.toml", 'language = "es"', 'language = "fr"')
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "language fr is not declared" in r.stdout


def test_conversation_category_checked(ws):
    edit(ws / "conversations" / "c-001.md", "category: home", "category: fmcg")
    r = run(ws, "validate.py")
    assert r.returncode == 1 and "bad category" in r.stdout


def test_no_workspace_is_an_error(tmp_path):
    r = run(tmp_path, "validate.py")
    assert r.returncode == 1 and "missing config/brand.toml" in r.stdout


# ---------------------------------------------------------------- status / stats
def test_build_status_collections(ws):
    r = run(ws, "build_status.py")
    assert r.returncode == 0, r.stderr
    idx = json.loads((ws / "status" / "index.json").read_text(encoding="utf-8"))["collections"]
    assert idx["groups"] == 3 and idx["conversations"] == 6 and idx["leads"] == 1 and idx["posts"] == 2
    funnel = json.loads((ws / "status" / "funnel.json").read_text(encoding="utf-8"))
    assert {f["stage"]: f["now"] for f in funnel}["X"] == 1
    summary = json.loads((ws / "status" / "summary.json").read_text(encoding="utf-8"))[0]
    assert summary["brand_name"] == "Demo Co" and [c["id"] for c in summary["categories"]] == ["home", "build"]
    assert all("id" in d for f in (ws / "status").glob("*.json") if f.name != "index.json"
               for d in json.loads(f.read_text(encoding="utf-8")))
    ready = {d["item"]: d["status"] for d in json.loads((ws / "status" / "readiness.json").read_text(encoding="utf-8"))}
    assert ready["At least one channel joined and active"] == "done"
    assert ready["Control center published"] == "open"


def test_funnel_stats_uses_catalog(ws):
    r = run(ws, "funnel_stats.py", "--since", "2025-01-01")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["conversations"] == 6 and out["funnel"]["reached"]["joined"] == 1
    assert set(out["by"]["category"]) == {"home", "build"}
    assert out["destination_joins"] == {"home": 6, "build": 1}


# ---------------------------------------------------------------- queue sheet / images
def test_queue_xlsx_labels_follow_ui_language(ws):
    from openpyxl import load_workbook
    q = next((ws / "runs").glob("*/queue.json"))
    edit(ws / "config" / "brand.toml", 'ui_language = "en"', 'ui_language = "vi"')
    r = run(ws, "build_queue_xlsx.py", str(q), "--no-previews")
    assert r.returncode == 0, r.stderr
    wb = load_workbook(q.with_suffix(".xlsx"))
    assert wb.sheetnames == ["Duyệt", "Cách dùng"]
    assert wb["Duyệt"]["J4"].value == "Quyết định"
    assert wb["Duyệt"]["G5"].value.startswith("Fixture meaning")


def test_compose_images_spec(tmp_path):
    from PIL import Image
    for n, color in (("t.png", "red"), ("a.png", "blue"), ("b.png", "green"), ("x.png", "gray")):
        Image.new("RGB", (400, 500), color).save(tmp_path / n)
    spec = {"jobs": [{"layout": "top_and_strip", "out": "o1.jpg", "top": "t.png", "top_crop_ratio": 0.8,
                      "products": ["a.png", "b.png"]},
                     {"layout": "two_stacked", "out": "o2.jpg", "a": "x.png", "a_y": 0.1, "b": "t.png", "b_y": 0.0}]}
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    r = run(tmp_path, "compose_images.py", str(tmp_path / "spec.json"))
    assert r.returncode == 0, r.stderr
    assert Image.open(tmp_path / "o1.jpg").size == (1080, 1350) and Image.open(tmp_path / "o2.jpg").size == (1080, 1350)


# ---------------------------------------------------------------- config_sync
CONFIGS = ["brand", "catalog", "funnel", "channels", "caps", "keywords"]


def test_round_trip_export_apply_is_lossless(ws):
    before = {n: toml(ws / "config" / f"{n}.toml") for n in CONFIGS}
    assert run(ws, "config_sync.py", "export").returncode == 0
    assert run(ws, "config_sync.py", "apply", "status/config").returncode == 0
    after = {n: toml(ws / "config" / f"{n}.toml") for n in CONFIGS}
    assert after == before
    assert run(ws, "validate.py").returncode == 0


def test_page_edit_reaches_toml_and_validates(ws):
    run(ws, "config_sync.py", "export")
    d = ws / "status" / "config"
    brand = json.loads((d / "brand.json").read_text(encoding="utf-8"))
    brand.update(brand_name="Page Edited Co", ui_language="es")
    (d / "brand.json").write_text(json.dumps(brand), encoding="utf-8")
    ch = json.loads((d / "channels.json").read_text(encoding="utf-8"))
    ch["channels"][2]["state"] = "active"
    ch["channels"][2]["joined_on"] = "2026-02-01"
    ch["channels"].append({**ch["channels"][0], "id": "A2", "name": "New group", "url": "https://www.facebook.com/groups/1000000000009"})
    (d / "channels.json").write_text(json.dumps(ch), encoding="utf-8")
    cat = json.loads((d / "catalog.json").read_text(encoding="utf-8"))
    cat["categories"].append({"id": "garden", "label": "Garden", "keywords": ["seeds"]})
    (d / "catalog.json").write_text(json.dumps(cat), encoding="utf-8")
    fun = json.loads((d / "funnel.json").read_text(encoding="utf-8"))
    fun["destinations"]["garden"] = {"type": "zalo", "name": "Garden", "url": "https://zalo.me/g/demo", "covers": ["seeds"], "tracked_base": ""}
    (d / "funnel.json").write_text(json.dumps(fun), encoding="utf-8")
    r = run(ws, "config_sync.py", "apply", "status/config")
    assert r.returncode == 0, r.stdout + r.stderr
    assert toml(ws / "config" / "brand.toml")["brand"]["brand_name"] == "Page Edited Co"
    assert [c["id"] for c in toml(ws / "config" / "channels.toml")["channel"]] == ["A1", "B1", "P1", "A2"]
    v = run(ws, "validate.py")
    assert v.returncode == 0, v.stdout
    assert run(ws, "build_status.py").returncode == 0
    groups = json.loads((ws / "status" / "groups.json").read_text(encoding="utf-8"))
    assert len(groups) == 4


def test_apply_preset_and_languages(ws):
    bundle = {"caps": {"id": "caps", "preset": "normal", "caps": toml(ws / "config" / "caps.toml")},
              "languages": {"id": "languages", "languages": {"en": {"native_review_done": True, "reviewer": "x"},
                                                              "vi": {"native_review_done": False, "reviewer": ""}}}}
    bundle["caps"]["caps"].pop("languages")
    (ws / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    assert run(ws, "config_sync.py", "apply", "bundle.json").returncode == 0
    caps = toml(ws / "config" / "caps.toml")
    assert caps["identity"]["personal"]["max_items_per_day"] == 12 and set(caps["languages"]) == {"en", "vi"}
    assert run(ws, "config_sync.py", "export").returncode == 0
    assert json.loads((ws / "status" / "config" / "caps.json").read_text(encoding="utf-8"))["preset"] == "normal"


def test_dry_run_changes_nothing(ws):
    run(ws, "config_sync.py", "export")
    d = ws / "status" / "config"
    brand = json.loads((d / "brand.json").read_text(encoding="utf-8"))
    brand["brand_name"] = "Changed"
    (d / "brand.json").write_text(json.dumps(brand), encoding="utf-8")
    r = run(ws, "config_sync.py", "apply", "status/config", "--dry-run")
    assert "would change" in r.stdout
    assert toml(ws / "config" / "brand.toml")["brand"]["brand_name"] == "Demo Co"


def test_invalid_page_data_is_caught_by_validate(ws):
    run(ws, "config_sync.py", "export")
    d = ws / "status" / "config"
    ch = json.loads((d / "channels.json").read_text(encoding="utf-8"))
    ch["channels"][0]["url"] = "http://evil.example.com/groups/1"
    (d / "channels.json").write_text(json.dumps(ch), encoding="utf-8")
    run(ws, "config_sync.py", "apply", "status/config")
    v = run(ws, "validate.py")
    assert v.returncode == 1 and "facebook.com" in v.stdout


def test_toml_writer_escapes_strings(ws):
    run(ws, "config_sync.py", "export")
    d = ws / "status" / "config"
    ch = json.loads((d / "channels.json").read_text(encoding="utf-8"))
    ch["channels"][0]["rules"] = 'Say "hi" \\ and\nnew line # not a comment'
    (d / "channels.json").write_text(json.dumps(ch), encoding="utf-8")
    run(ws, "config_sync.py", "apply", "status/config")
    assert toml(ws / "config" / "channels.toml")["channel"][0]["rules"] == ch["channels"][0]["rules"]


def test_facts_document_round_trip_and_bookkeeping_keys(ws):
    facts = {"id": "facts", "_updated": "2026-01-01T00:00:00Z", "facts": [
        {"id": "f1", "scope": "company", "text": "We ship  by\npallet.", "approved": True, "_x": 1},
        {"id": "f2", "scope": "home", "text": "Detergent comes in 5 kg bags.", "approved": True},
        {"id": "f3", "scope": "home", "text": "Maybe a new soap line.", "approved": False}]}
    brand = json.loads((run(ws, "config_sync.py", "export") and (ws / "status/config/brand.json")).read_text(encoding="utf-8"))
    brand["_updated"] = "2026-01-01T00:00:00Z"
    (ws / "bundle.json").write_text(json.dumps({"facts": facts, "brand": brand}), encoding="utf-8")
    assert run(ws, "config_sync.py", "apply", "bundle.json").returncode == 0
    assert "_updated" not in (ws / "config" / "brand.toml").read_text(encoding="utf-8")
    approved = (ws / "knowledge" / "facts.md").read_text(encoding="utf-8")
    assert "status: APPROVED" in approved and "- We ship by pallet." in approved and "## home" in approved
    assert "status: DRAFT" in (ws / "knowledge" / "facts-draft.md").read_text(encoding="utf-8")
    assert run(ws, "validate.py").returncode == 0
    run(ws, "config_sync.py", "export")
    out = json.loads((ws / "status/config/facts.json").read_text(encoding="utf-8"))["facts"]
    assert [(f["scope"], f["approved"]) for f in out] == [("company", True), ("home", True), ("home", False)]
    # removing every fact removes the files
    (ws / "bundle.json").write_text(json.dumps({"facts": {"id": "facts", "facts": []}}), encoding="utf-8")
    run(ws, "config_sync.py", "apply", "bundle.json")
    assert not (ws / "knowledge" / "facts.md").exists() and not (ws / "knowledge" / "facts-draft.md").exists()
