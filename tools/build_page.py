"""Build plugins/social-seeding/page/control-center.html from control-center.src.html and i18n/*.json.

Usage: python tools/build_page.py [--check]
--check exits 1 when the built file is out of date or an i18n key is missing (used by the tests).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "social-seeding"
SRC = PLUGIN / "page" / "control-center.src.html"
OUT = PLUGIN / "page" / "control-center.html"
LANGS = ["en", "vi", "es"]

# t("prefix" + value) call sites: the value sets
DYNAMIC = {
    "f_": ["brand_name", "rep_name", "disclosure", "audience_timezone", "operator_timezone", "daily_run", "hot_replies"],
    "step_": ["brand", "categories", "funnel", "languages", "knowledge", "channels", "caps", "schedule"],
    "stage_": ["0", "1", "2", "3", "4", "X"],
    "dest_": ["whatsapp", "telegram", "zalo", "messenger", "website"],
    "kind_": ["discussion", "board", "page", "daily-run", "hot-replies", "check-replies", "health-check"],
    "state_": ["not_joined", "pending", "active", "cooldown", "retired"],
    "tri_": ["yes", "no", "unknown"],
    "preset_": ["careful", "normal", "custom"],
    "dec_": ["approve", "edit", "drop"],
    "dash_": ["overview", "conversations", "leads", "posts", "runs", "health"],
    "req_": ["pending", "handled"],
    "type_": ["reply", "comment", "post", "offer_post", "invite", "dm_invite", "dm_inbound"],
    "cap_": ["identity_personal_max_items_per_day", "identity_personal_max_offer_posts_per_day", "per_group_max_items_per_day",
             "content_max_link_share", "per_group_warmup_days"],
}
EXTRA = ["step_%s_lede" % s for s in DYNAMIC["step_"]] + ["preset_careful_d", "preset_normal_d"]


def load() -> dict[str, dict]:
    return {l: json.loads((PLUGIN / "i18n" / f"{l}.json").read_text(encoding="utf-8")) for l in LANGS}


def needed_keys(src: str) -> set[str]:
    keys = set(re.findall(r'\bt\("([a-z_0-9]+)"', src))
    keys = {k for k in keys if k not in DYNAMIC}      # bare prefixes such as "f_" are dynamic call sites
    for prefix, vals in DYNAMIC.items():
        keys |= {prefix + v for v in vals}
    return keys | set(EXTRA)


def problems(src: str, i18n: dict[str, dict]) -> list[str]:
    out = []
    base = set(i18n["en"])
    for l in LANGS[1:]:
        for k in sorted(base - set(i18n[l])):
            out.append(f"{l}: missing key {k}")
        for k in sorted(set(i18n[l]) - base):
            out.append(f"{l}: extra key {k}")
    for k in sorted(needed_keys(src) - base):
        out.append(f"en: page uses missing key {k}")
    for l in LANGS:       # placeholders must match across languages
        for k, v in i18n[l].items():
            if k in i18n["en"] and sorted(re.findall(r"\{\w+\}", v)) != sorted(re.findall(r"\{\w+\}", i18n["en"][k])):
                out.append(f"{l}: placeholders of {k} differ from en")
    return out


def build() -> str:
    src = SRC.read_text(encoding="utf-8")
    i18n = load()
    data = json.dumps(i18n, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return src.replace("/*I18N*/{}", data, 1)


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    errs = problems(src, load())
    for e in errs:
        print("ERROR", e)
    html = build()
    if "--check" in sys.argv:
        if errs or not OUT.exists() or OUT.read_text(encoding="utf-8") != html:
            print("control-center.html is out of date: run python tools/build_page.py")
            return 1
        return 0
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html)} bytes), {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
