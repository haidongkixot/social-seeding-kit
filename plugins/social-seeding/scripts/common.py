"""Shared helpers: find the workspace, load TOML configs, parse markdown front matter. Stdlib only.

The workspace is the customer's data folder (config/, knowledge/, runs/ ...). It is found from the
SSK_WORKSPACE environment variable, else by walking up from the current directory to the first
folder that has config/brand.toml.
"""
from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path


def find_workspace() -> Path:
    env = os.environ.get("SSK_WORKSPACE")
    if env:
        return Path(env).resolve()
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / "config" / "brand.toml").exists():
            return p
    return cur


ROOT = find_workspace()


def load_toml(name: str, required: bool = True) -> dict:
    path = ROOT / "config" / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f"missing config/{name} in workspace {ROOT}")
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def channels() -> dict[str, dict]:
    return {c["id"]: c for c in load_toml("channels.toml").get("channel", [])}


def categories() -> list[dict]:
    return load_toml("catalog.toml").get("category", [])


def category_ids() -> list[str]:
    return [c["id"] for c in categories()]


def brand() -> dict:
    return load_toml("brand.toml").get("brand", {})


_COMMENT = re.compile(r"\s{2,}#.*$")


def front_matter(path: Path) -> tuple[dict, str]:
    """Return (fields, body) for a file that starts with a '---' front-matter block.

    Values are plain strings; a trailing '  # comment' (two+ spaces before #) is removed;
    surrounding quotes are stripped.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = _COMMENT.sub("", value).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return fields, text[end + 4 :]
