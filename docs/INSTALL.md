# Install

The kit is a Claude Code plugin marketplace (`social-seeding-kit`) holding one plugin (`social-seeding`).

## Requirements
- Claude Code, with the Claude in Chrome extension connected to the browser where you are signed in to Facebook.
- Python 3.11 or newer, with `pip install openpyxl Pillow` (and `tzdata` on Windows).
- `git`.
- Chrome or Edge on the same computer (headless, for approval-sheet previews). Set `SSK_BROWSER` to the executable if it is not found.
- Optional: the Gmail and Google Drive connectors.
- To publish the control center you need a Claude account that can publish artifacts with the `db` and `user` capabilities.

## Install the plugin
From a local copy (version 0.1.0 is local only):
```
/plugin marketplace add D:\path\to\social-seeding-kit
/plugin install social-seeding@social-seeding-kit
```
When the repository is on GitHub: `/plugin marketplace add <owner>/<repo>`.

## First run
1. Create an empty folder for the brand and start Claude Code in it.
2. Run `/social-seeding:seeding-setup` (plugin skills are namespaced; `/seeding-setup` works when the name is not ambiguous).
3. Follow the prompts. The control center URL is stored in `config/brand.toml`.

## Updating
Update the plugin with `/plugin` (marketplace update). The workspace is separate, so your config, facts, conversations and reports are not touched. Release notes are in [CHANGELOG.md](CHANGELOG.md).

## Working on the kit itself
```
pip install pytest openpyxl Pillow tzdata
python tools/make_demo.py            # the "Demo Co" demo workspace in demo/ (synthetic data)
python -m pytest -q                  # scripts, setup, control-center page (needs Chrome or Edge for the page tests)
python tools/build_page.py           # rebuild page/control-center.html after editing page/*.src.html or i18n/*.json
python tools/render_page.py shots <dir> --lang en|vi|es    # screenshots with a stubbed artifact runtime
```
