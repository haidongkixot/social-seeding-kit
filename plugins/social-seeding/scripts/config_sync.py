"""Convert between the control center's JSON documents and the workspace TOML.

Usage:
  python scripts/config_sync.py export [--out status/config]   workspace TOML -> JSON documents
  python scripts/config_sync.py apply <dir-or-bundle.json> [--dry-run]
                                                               JSON documents -> config/*.toml (then run validate.py)

Documents (the page keeps them in its database under collection "config"):
  brand      {"id": "brand", ...brand.toml [brand] keys}
  catalog    {"id": "catalog", "categories": [{id,label,keywords}]}
  funnel     {"id": "funnel", "destinations": {<cat>: {type,name,url,covers,tracked_base}}, "member_counts": [...]}
  channels   {"id": "channels", "channels": [{...channel keys}]}
  caps       {"id": "caps", "preset": "careful|normal", "caps": {...full caps.toml tree}}
  keywords   {"id": "keywords", ...keywords.toml tree}
  languages  {"id": "languages", "languages": {<code>: {native_review_done, reviewer}}}   (lives in caps.toml)
  facts      {"id": "facts", "facts": [{id, scope, text, approved}]}   (scope: "company" or a category id)
             -> knowledge/facts.md (approved) and knowledge/facts-draft.md (not yet approved)
Keys starting with "_" (the page's bookkeeping, e.g. _updated, _synced) are never written to TOML.

A bundle is one JSON object {"brand": doc, "catalog": doc, ...}; a directory holds <name>.json files.
Only the keys present are applied; the safety rules (SAFETY.md) are not part of any document.
Stdlib only: the TOML writer below handles the shapes used by this kit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_toml  # noqa: E402

DOCS = ["brand", "catalog", "funnel", "channels", "caps", "keywords", "languages", "facts"]
PRESETS = {
    "careful": {"identity.personal.max_items_per_day": 8, "identity.personal.max_offer_posts_per_day": 2,
                "per_group.max_items_per_day": 2, "content.max_link_share": 0.30, "per_group.warmup_days": 14},
    "normal": {"identity.personal.max_items_per_day": 12, "identity.personal.max_offer_posts_per_day": 3,
               "per_group.max_items_per_day": 3, "content.max_link_share": 0.40, "per_group.warmup_days": 10},
}
CHANNEL_KEYS = ["id", "name", "url", "kind", "identity", "language", "fit", "city", "members", "posts_per_day",
                "promo_posts", "links", "rules", "wave", "state", "joined_on"]
CATALOG_KEYS = ["id", "label", "keywords"]
DEST_KEYS = ["type", "name", "url", "covers", "tracked_base"]


# ---------------------------------------------------------------- TOML writer
def _val(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_val(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{_key(k)} = {_val(x)}" for k, x in v.items()) + " }"
    raise TypeError(f"cannot write {type(v).__name__} to TOML")


def _key(k: str) -> str:
    return k if k.replace("_", "").replace("-", "").isalnum() else json.dumps(k, ensure_ascii=False)


def _table(lines: list[str], path: str, d: dict) -> None:
    """Write dict d as [path] with scalars first, then nested dicts as sub-tables."""
    scalars = {k: v for k, v in d.items() if not isinstance(v, dict) or path == "languages"}
    subs = {k: v for k, v in d.items() if k not in scalars}
    if scalars or not subs:
        lines.append(f"[{path}]")
        for k, v in scalars.items():
            lines.append(f"{_key(k)} = {_val(v)}")
        lines.append("")
    for k, v in subs.items():
        _table(lines, f"{path}.{_key(k)}", v)


def dumps_tree(tree: dict, header: str = "") -> str:
    lines = [header.rstrip(), ""] if header else []
    for k, v in tree.items():
        if isinstance(v, dict):
            _table(lines, _key(k), v)
        else:
            lines.append(f"{_key(k)} = {_val(v)}")
    return "\n".join(lines).rstrip() + "\n"


def dumps_array(name: str, rows: list[dict], key_order: list[str], header: str = "") -> str:
    lines = [header.rstrip(), ""] if header else []
    for r in rows:
        lines.append(f"[[{name}]]")
        for k in key_order + [k for k in r if k not in key_order]:
            if k in r:
                lines.append(f"{_key(k)} = {_val(r[k])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- export
def export_docs() -> dict[str, dict]:
    caps = load_toml("caps.toml")
    languages = caps.pop("languages", {})
    funnel = load_toml("funnel.toml")
    return {
        "brand": {"id": "brand", **load_toml("brand.toml").get("brand", {})},
        "catalog": {"id": "catalog", "categories": load_toml("catalog.toml").get("category", [])},
        "funnel": {"id": "funnel", "destinations": funnel.get("destination", {}),
                   "member_counts": funnel.get("member_count", [])},
        "channels": {"id": "channels", "channels": load_toml("channels.toml").get("channel", [])},
        "caps": {"id": "caps", "preset": detect_preset(caps), "caps": caps},
        "keywords": {"id": "keywords", **load_toml("keywords.toml", required=False)},
        "languages": {"id": "languages", "languages": languages},
        "facts": {"id": "facts", "facts": read_facts()},
    }


def read_facts() -> list[dict]:
    """Parse knowledge/facts.md and facts-draft.md: '## scope' sections of '- text' bullets."""
    out = []
    for name, approved in (("facts.md", True), ("facts-draft.md", False)):
        p = ROOT / "knowledge" / name
        if not p.exists():
            continue
        scope = "company"
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                scope = line[3:].strip()
            elif line.startswith("- ") and line[2:].strip():
                out.append({"id": f"f{len(out) + 1}", "scope": scope, "text": line[2:].strip(), "approved": approved})
    return out


def write_facts(facts: list[dict]) -> dict[str, str]:
    today = dt.date.today().isoformat()
    files = {}
    for name, approved in (("facts.md", True), ("facts-draft.md", False)):
        rows = [f for f in facts if bool(f.get("approved")) == approved and str(f.get("text", "")).strip()]
        if not rows:
            continue
        status = f"APPROVED (owner, control center, {today})" if approved else "DRAFT"
        lines = ["---", f"status: {status}", f"valid_from: {today}", "valid_to:", "---",
                 "# Facts written on the control center", ""]
        for scope in dict.fromkeys(f.get("scope", "company") for f in rows):
            lines += [f"## {scope}"] + [f"- {' '.join(str(f['text']).split())}" for f in rows if f.get("scope", "company") == scope] + [""]
        files[name] = chr(10).join(lines)
    return files


def detect_preset(caps: dict) -> str:
    def get(path: str):
        node = caps
        for p in path.split("."):
            node = node.get(p) if isinstance(node, dict) else None
        return node
    for name, vals in PRESETS.items():
        if all(get(k) == v for k, v in vals.items()):
            return name
    return "custom"


# ---------------------------------------------------------------- apply
def _strip_id(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "id" and not k.startswith("_")}


def _clean(value):
    """Drop page bookkeeping keys (leading underscore) at any depth."""
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def apply_docs(docs: dict[str, dict], dry_run: bool = False) -> list[str]:
    """Write the TOML files for the documents present. Returns the list of files changed."""
    cfg = ROOT / "config"
    docs = {k: _clean(v) if k != "facts" else v for k, v in docs.items()}
    out: dict[str, str] = {}
    cur_caps = load_toml("caps.toml")

    if "brand" in docs:
        out["brand.toml"] = dumps_tree({"brand": _strip_id(docs["brand"])},
                                       "# Who we are and how the system talks. Written by sync-control from the control center.")
    if "catalog" in docs:
        out["catalog.toml"] = dumps_array("category", docs["catalog"]["categories"], CATALOG_KEYS,
                                          "# What you sell, as categories. Written by sync-control from the control center.")
    if "funnel" in docs:
        f = docs["funnel"]
        dest = {c: {k: d[k] for k in DEST_KEYS if k in d} for c, d in f.get("destinations", {}).items()}
        text = dumps_tree({"destination": dest}, "# End of the funnel: one destination per category. Written by sync-control.")
        text += "\n" + dumps_array("member_count", f.get("member_counts", []), ["date"])
        out["funnel.toml"] = text
    if "channels" in docs:
        out["channels.toml"] = dumps_array("channel", docs["channels"]["channels"], CHANNEL_KEYS,
                                           "# Facebook groups and fanpages. Written by sync-control from the control center.")
    if "caps" in docs or "languages" in docs:
        tree = dict(docs["caps"]["caps"]) if "caps" in docs else {k: v for k, v in cur_caps.items() if k != "languages"}
        if "caps" in docs and docs["caps"].get("preset") in PRESETS:
            for path, v in PRESETS[docs["caps"]["preset"]].items():
                node = tree
                *parents, last = path.split(".")
                for p in parents:
                    node = node.setdefault(p, {})
                node[last] = v
        tree.pop("languages", None)
        langs = docs["languages"]["languages"] if "languages" in docs else cur_caps.get("languages", {})
        tree["languages"] = langs
        out["caps.toml"] = dumps_tree(tree, "# Risk-manager limits and languages. Written by sync-control from the control center.")
    if "keywords" in docs:
        out["keywords.toml"] = dumps_tree(_strip_id(docs["keywords"]),
                                          "# Search terms and intent signals. Written by sync-control from the control center.")

    if "facts" in docs:
        for name, text in write_facts(_clean(docs["facts"].get("facts", []))).items():
            out[f"../knowledge/{name}"] = text
        for name in ("facts.md", "facts-draft.md"):
            if f"../knowledge/{name}" not in out and (ROOT / "knowledge" / name).exists() and not dry_run:
                (ROOT / "knowledge" / name).unlink()

    changed = []
    for name, text in out.items():
        path = cfg / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            changed.append(f"config/{name}".replace("config/../", ""))
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return changed


def load_docs(src: Path) -> dict[str, dict]:
    if src.is_dir():
        return {n: json.loads((src / f"{n}.json").read_text(encoding="utf-8-sig"))
                for n in DOCS if (src / f"{n}.json").exists()}
    data = json.loads(src.read_text(encoding="utf-8-sig"))
    return {n: data[n] for n in DOCS if n in data}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--out", default="status/config")
    a = sub.add_parser("apply")
    a.add_argument("src")
    a.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.cmd == "export":
        out = ROOT / args.out
        out.mkdir(parents=True, exist_ok=True)
        for name, doc in export_docs().items():
            (out / f"{name}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"exported {len(DOCS)} documents to {out}")
        return 0
    docs = load_docs(Path(args.src))
    if not docs:
        print("no config documents found")
        return 1
    changed = apply_docs(docs, args.dry_run)
    print(("would change: " if args.dry_run else "changed: ") + (", ".join(changed) or "nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
