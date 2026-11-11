"""Copy the Thai Binh agents and skills into the plugin and apply a find -> replace mapping table.

Usage: python tools/generalize.py <tb-claude-dir> <plugin-dir>
Read-only on the source. The result is a first pass; the prompts are then reviewed by hand.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

LITERAL = [
    ("Read `CLAUDE.md` first; its hard rules apply to you.",
     "Read the plugin's `SAFETY.md` (in `${CLAUDE_PLUGIN_ROOT}`) and the workspace `CLAUDE.md` first; the safety rules apply to you."),
    ("Read `CLAUDE.md`, ", "Read the plugin's `SAFETY.md`, the workspace `CLAUDE.md`, "),
    ("CLAUDE.md rule", "SAFETY.md rule"),
    ("CLAUDE.md's hard rules", "SAFETY.md's rules"),
    ("`CLAUDE.md`", "`SAFETY.md`"),
    ("Thai Binh Corp's", "the brand's"),
    ("Thai Binh Corp", "the brand"),
    ("Thai Binh's", "the brand's"),
    ("Thai Binh", "the brand"),
    ("Hải's", "the owner's"),
    ("Hai's", "the owner's"),
    ("Hải", "the owner"),
    ("Havana daytime", "audience daytime"),
    ("Havana", "the audience timezone"),
    ("es-419", "the channel's language"),
    ("python scripts/", "python \"${CLAUDE_PLUGIN_ROOT}/scripts/"),
    ("WhatsApp group", "funnel destination"),
    ("WhatsApp", "funnel destination"),
    ("`fmcg`, `construction` or `both`", "a catalog category id, `both` or `unknown`"),
    ("fmcg or construction", "a catalog category"),
    ("fmcg", "<category>"),
    ("construction", "<category>"),
    ("config/whatsapp.toml", "config/funnel.toml"),
    ("MIRIKO", "<product>"),
    ("Cuba", "<country>"),
]


def fix_script_paths(text: str) -> str:
    # close the quote opened by the python-scripts replacement: ...scripts/name.py -> ...scripts/name.py"
    return re.sub(r'(\$\{CLAUDE_PLUGIN_ROOT\}/scripts/[\w.-]+\.py)', r'\1"', text)


def main(src: str, dst: str) -> int:
    srcp, dstp = Path(src), Path(dst)
    for kind in ("agents", "skills"):
        if (dstp / kind).exists():
            shutil.rmtree(dstp / kind)
        shutil.copytree(srcp / kind, dstp / kind)
    skip = {"sync-drive", "status-page"}   # rewritten by hand as sync-control / publish-status
    for s in skip:
        shutil.rmtree(dstp / "skills" / s, ignore_errors=True)
    for f in list((dstp / "agents").glob("*.md")) + list((dstp / "skills").glob("*/SKILL.md")):
        t = f.read_text(encoding="utf-8-sig")
        for a, b in LITERAL:
            t = t.replace(a, b)
        f.write_text(fix_script_paths(t), encoding="utf-8")
    print("copied and mapped")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
