"""Validate the workspace configs, knowledge and conversations. Exit 1 on errors; warnings are informational.

Usage: python scripts/validate.py   (run inside the workspace, or set SSK_WORKSPACE)
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, front_matter, load_toml  # noqa: E402

errors: list[str] = []
warnings: list[str] = []

KINDS = {"discussion", "board", "page"}
IDENTITIES = {"personal", "page"}
TRISTATE = {"yes", "no", "unknown"}
WAVES = {"pilot", "w2", "w3", "w4"}
STATES = {"not_joined", "pending", "active", "cooldown", "retired"}
DEST_TYPES = {"whatsapp", "telegram", "zalo", "messenger", "website"}
UI_LANGS = {"en", "vi", "es"}
STAGES = {"0", "1", "2", "3", "4", "X"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
ID = re.compile(r"^[a-z][a-z0-9_-]*$")
TZ = re.compile(r"^[A-Za-z_]+(/[A-Za-z0-9_+-]+)+$|^UTC$")
FB_URL = re.compile(r"^https://(www\.|m\.|web\.)?facebook\.com/\S+")
REQUIRED = ["id", "name", "url", "kind", "identity", "language", "fit", "city", "members",
            "posts_per_day", "promo_posts", "links", "rules", "wave", "state", "joined_on"]
RESERVED_CATS = {"both", "unknown"}
DEST_URL = {"whatsapp": "https://chat.whatsapp.com/", "telegram": "https://t.me/",
            "zalo": "https://zalo.me/", "messenger": "https://m.me/"}


def check_brand() -> dict:
    b = load_toml("brand.toml").get("brand", {})
    for k in ("brand_name", "rep_name", "disclosure", "ui_language", "audience_timezone", "operator_timezone"):
        if not str(b.get(k, "")).strip():
            errors.append(f"brand: missing '{k}'")
    if b.get("ui_language") and b["ui_language"] not in UI_LANGS:
        errors.append(f"brand: ui_language must be one of {sorted(UI_LANGS)}")
    for k in ("audience_timezone", "operator_timezone"):
        if b.get(k) and not TZ.match(b[k]):
            errors.append(f"brand: {k} must be an IANA name like Europe/Madrid")
    d = b.get("disclosure", "")
    if d and "{rep}" not in d and "{brand}" not in d:
        warnings.append("brand: disclosure has no {rep} or {brand} placeholder")
    if not b.get("owner_email"):
        warnings.append("brand: owner_email empty (reply alerts cannot be sent)")
    if not b.get("control_center_url"):
        warnings.append("brand: control_center_url empty (publish the control center)")
    return b


def check_catalog() -> list[str]:
    cats = load_toml("catalog.toml").get("category", [])
    if not cats:
        errors.append("catalog: at least one [[category]] is required")
    ids = Counter(c.get("id") for c in cats)
    for cid, n in ids.items():
        if n > 1:
            errors.append(f"catalog: duplicate id {cid}")
    for c in cats:
        cid = c.get("id", "?")
        if not ID.match(str(c.get("id", ""))):
            errors.append(f"catalog {cid}: id must be lowercase letters/digits/_/-")
        if c.get("id") in RESERVED_CATS:
            errors.append(f"catalog {cid}: id is reserved")
        if not c.get("label"):
            errors.append(f"catalog {cid}: missing label")
        if not c.get("keywords"):
            warnings.append(f"catalog {cid}: no keywords")
    return [c["id"] for c in cats if "id" in c]


def check_funnel(cat_ids: list[str]) -> None:
    f = load_toml("funnel.toml")
    dest = f.get("destination", {})
    for cid in cat_ids:
        d = dest.get(cid)
        if not d:
            errors.append(f"funnel: missing [destination.{cid}]")
            continue
        t = d.get("type")
        if t not in DEST_TYPES:
            errors.append(f"funnel {cid}: type {t!r} not in {sorted(DEST_TYPES)}")
            continue
        url = str(d.get("url", ""))
        if not url.startswith("https://"):
            errors.append(f"funnel {cid}: url must start with https://")
        elif t in DEST_URL and not url.startswith(DEST_URL[t]):
            errors.append(f"funnel {cid}: a {t} url must start with {DEST_URL[t]}")
        if not d.get("tracked_base"):
            warnings.append(f"funnel {cid}: no tracked_base - clicks per channel will not be measured")
    for cid in dest:
        if cid not in cat_ids:
            errors.append(f"funnel: destination.{cid} is not a catalog category")
    counts = f.get("member_count", [])
    if not any(any(m.get(c, 0) for c in cat_ids) for m in counts):
        warnings.append("funnel: no real member counts yet (joins cannot be measured)")


def check_channels(caps: dict, cat_ids: list[str], langs: set[str]) -> dict[str, dict]:
    chans = load_toml("channels.toml").get("channel", [])
    ids = Counter(c.get("id") for c in chans)
    for cid, n in ids.items():
        if n > 1:
            errors.append(f"channels: duplicate id {cid}")
    page_enabled = caps.get("identity", {}).get("page", {}).get("enabled", False)
    for c in chans:
        cid = c.get("id", "?")
        for k in REQUIRED:
            if k not in c:
                errors.append(f"channels {cid}: missing '{k}'")
        if not FB_URL.match(str(c.get("url", ""))):
            errors.append(f"channels {cid}: url must be a facebook.com group or page URL")
        elif c.get("kind") != "page" and "/groups/" not in c["url"]:
            errors.append(f"channels {cid}: a group url must contain /groups/ (use kind = \"page\" for fanpages)")
        for key, allowed in [("kind", KINDS), ("identity", IDENTITIES), ("promo_posts", TRISTATE),
                             ("links", TRISTATE), ("wave", WAVES), ("state", STATES)]:
            if c.get(key) not in allowed:
                errors.append(f"channels {cid}: {key}={c.get(key)!r} not in {sorted(allowed)}")
        lang = c.get("language")
        if not LANG.match(str(lang or "")):
            errors.append(f"channels {cid}: language {lang!r} is not a BCP-47 code")
        elif lang not in langs:
            errors.append(f"channels {cid}: language {lang} is not declared in caps.toml [languages]")
        bad_fit = set(c.get("fit", [])) - set(cat_ids)
        if bad_fit or not c.get("fit"):
            errors.append(f"channels {cid}: fit must be a non-empty subset of the catalog {sorted(cat_ids)}")
        if c.get("identity") == "page" and not page_enabled:
            errors.append(f"channels {cid}: identity 'page' but [identity.page] enabled = false")
        jo = c.get("joined_on", "")
        if c.get("state") in {"active", "cooldown"}:
            if not DATE.match(jo):
                errors.append(f"channels {cid}: state {c['state']} needs joined_on YYYY-MM-DD")
        elif jo and not DATE.match(jo):
            errors.append(f"channels {cid}: joined_on must be YYYY-MM-DD or empty")
        if c.get("kind") == "board" and c.get("promo_posts") == "unknown" and c.get("state") == "active":
            warnings.append(f"channels {cid}: active board with promo_posts unknown (offer posts blocked)")
    waves = Counter(c.get("wave") for c in chans)
    active = sum(1 for c in chans if c.get("state") == "active")
    print(f"channels: {len(chans)} total | waves {dict(waves)} | active {active}")
    return {c["id"]: c for c in chans if "id" in c}


def check_caps(caps: dict) -> set[str]:
    for path in [("identity", "personal", "max_items_per_day"), ("per_group", "max_items_per_day"),
                 ("content", "max_link_share"), ("content", "max_unanswered_turns"), ("health", "red_pause_hours")]:
        node = caps
        for p in path:
            node = node.get(p) if isinstance(node, dict) else None
        if node is None:
            errors.append(f"caps: missing {'.'.join(path)}")
    langs = caps.get("languages", {})
    if not langs:
        errors.append("caps: [languages] needs at least one language")
    for lang, v in langs.items():
        if not LANG.match(lang):
            errors.append(f"caps: language key {lang!r} is not a BCP-47 code")
        if not v.get("native_review_done"):
            warnings.append(f"caps: language {lang} has no native review yet (live posting in {lang} blocked)")
    share = caps.get("content", {}).get("max_link_share")
    if share is not None and not 0 <= share <= 1:
        errors.append("caps: content.max_link_share must be between 0 and 1")
    return set(langs)


def check_keywords(cat_ids: list[str], langs: set[str]) -> None:
    kw = load_toml("keywords.toml", required=False)
    if not kw:
        warnings.append("keywords: no keywords.toml (the scout has no search terms)")
        return
    for cid in kw.get("category", {}):
        if cid not in cat_ids:
            errors.append(f"keywords: [category.{cid}] is not a catalog category")
    groups = [("demand", kw.get("demand", {})), ("cities", kw.get("cities", {})),
              ("signals.qualified", kw.get("signals", {}).get("qualified", {})),
              ("signals.negative", kw.get("signals", {}).get("negative", {}))]
    groups += [(f"category.{c}", v) for c, v in kw.get("category", {}).items()]
    for name, g in groups:
        for lang, words in g.items():
            if lang not in langs:
                errors.append(f"keywords [{name}]: language {lang} is not declared in caps.toml")
            if not isinstance(words, list) or not all(isinstance(w, str) for w in words):
                errors.append(f"keywords [{name}].{lang}: must be a list of strings")


def check_knowledge() -> None:
    today = dt.date.today()
    folder = ROOT / "knowledge"
    if not folder.exists():
        warnings.append("knowledge/ missing")
        return
    for p in sorted(folder.rglob("*.md")):
        if p.name == "README.md":
            continue
        rel = p.relative_to(ROOT).as_posix()
        fm, body = front_matter(p)
        status = fm.get("status", "")
        if not status:
            errors.append(f"{rel}: missing front matter 'status'")
            continue
        if not (status == "DRAFT" or status.startswith("APPROVED")):
            errors.append(f"{rel}: status must be DRAFT or 'APPROVED (name, date)'")
        if status == "DRAFT":
            warnings.append(f"{rel}: DRAFT (not usable for live items)")
        vt = fm.get("valid_to", "")
        if vt:
            if not DATE.match(vt):
                errors.append(f"{rel}: valid_to must be YYYY-MM-DD")
            elif dt.date.fromisoformat(vt) < today:
                errors.append(f"{rel}: expired (valid_to {vt}) - update or archive")
        n_confirm = body.count("[CONFIRM")
        if n_confirm:
            warnings.append(f"{rel}: {n_confirm} [CONFIRM] item(s) open")


def check_conversations(chans: dict[str, dict], cat_ids: list[str]) -> None:
    folder = ROOT / "conversations"
    if not folder.exists():
        return
    stages = Counter()
    for p in sorted(folder.glob("*.md")):
        fm, _ = front_matter(p)
        rel = p.relative_to(ROOT).as_posix()
        for k in ("id", "channel", "thread_url", "identity", "playbook", "category", "stage", "max_stage"):
            if k not in fm:
                errors.append(f"{rel}: missing '{k}'")
        if fm.get("channel") and fm["channel"] not in chans:
            errors.append(f"{rel}: unknown channel {fm['channel']}")
        if fm.get("stage") not in STAGES:
            errors.append(f"{rel}: stage must be one of {sorted(STAGES)}")
        if fm.get("category") not in set(cat_ids) | RESERVED_CATS:
            errors.append(f"{rel}: bad category {fm.get('category')!r}")
        stages[fm.get("stage")] += 1
    if stages:
        print(f"conversations by stage: {dict(sorted(stages.items()))}")


def main() -> int:
    print(f"workspace: {ROOT}")
    try:
        check_brand()
        cat_ids = check_catalog()
        caps = load_toml("caps.toml")
        langs = check_caps(caps)
        check_funnel(cat_ids)
        chans = check_channels(caps, cat_ids, langs)
        check_keywords(cat_ids, langs)
        check_knowledge()
        check_conversations(chans, cat_ids)
    except FileNotFoundError as e:
        errors.append(str(e))
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
