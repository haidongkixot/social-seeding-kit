# Build brief (from Hải, 2026-11-12)

Build the "Social Seeding Kit" Claude Code plugin by following `docs/PLAN.md` (approved by Hải). Do phases 1–5 in order. Phase 6 (migrating Thai Binh) is out of scope.

## Source (read only)
`D:/Claude Projects/tb-social-seeding` is a live project. Never write, move, delete or commit anything there.
- Copy what you need into this repo with Python, then work on the copies.

## Isolation
- No browser, Facebook, Google Drive, Gmail or claude.ai artifacts: this process runs without MCP servers.
- The control-center page is tested as a local HTML file. Render it with headless Edge, from Python's `subprocess`:
  `"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --screenshot=<abs path> --window-size=1280,1600 --user-data-dir=<temp dir> file:///...`
  Mock the artifact runtime (`window.claude` / the db calls) with a small local stub, so the page renders with fixture data.
  Publishing a real "SSK test" artifact is left for Hải or a later session; just note it in the report.
- Test with a demo workspace (`demo/`, brand "Demo Co") and fixture data.
  - Copies of TB `runs/`, `conversations/` and `leads.csv` may go into `fixtures/`, which must be git-ignored because it holds real names.
- No GitHub push.

## Save tokens: local compute first
- Generalize with Python scripts:
  - copytree, then a mapping table of find → replace for brand, people, places and URLs;
  - regex for the hard-coded sets.
  - Don't read and retype whole files.
- Read files in parts (grep, head). Keep the context small.
- Verify locally:
  - `python scripts/validate.py` on `demo/`;
  - `python -m pytest -q` (a small suite for the scripts);
  - a grep for leftover TB strings: `Thai Binh|Hải|Hai |Havana|MIRIKO|SUCHEL|eagodi|PmmX1q|Cuba` inside `plugins/social-seeding/` (Cuba is allowed only in the es-419 style example);
  - the headless Edge screenshot of the page.
- The design work that needs judgement: `SAFETY.md`, the generic agent and skill prompts, the control-center page, and the i18n strings (en/vi/es).

## Deliverables
- **Plugin layout:** as in `docs/PLAN.md`, "Shape of the package".
- **Config schema:** `brand.toml`, `catalog.toml`, `funnel.toml`, `channels.toml` (groups and fanpages), `caps.toml`, `keywords.toml`, `languages`. All validated by `validate.py`.
- **`config_sync.py`:** converts between the page's JSON documents and the workspace TOML. Test the round trip with fixture JSON.
- **Commits:** at the end of each phase. Each message ends with:
  `Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`
- **When done:** tag `v0.1.0` and write `docs/REPORT.md`, a short report covering what works, what was tested and how, and what remains (for example publishing the real artifact, the GitHub push, the Thai Binh migration).
