# Build report: Social Seeding Kit v0.1.0 (2026-11-12)

Phases 1-5 of `docs/PLAN.md` are done and tagged `v0.1.0`. Phase 6 (migrating Thai Binh) was out of scope. Nothing was pushed to GitHub.

## What works
- **Plugin** `plugins/social-seeding` with 6 agents, 9 skills, `SAFETY.md`, scripts, templates and the page, plus a one-plugin marketplace at `.claude-plugin/marketplace.json`.
- **Config schema** (`brand`, `catalog`, `funnel`, `channels`, `caps` with open `[languages]`, `keywords`), all validated by `validate.py`: categories are data (no fixed fmcg/construction), funnel destinations are whatsapp/telegram/zalo/messenger/website, channels accept groups and fanpages (`kind = "page"`), languages are any BCP-47 code with its own review flag.
- **Scripts** are workspace-driven (cwd or `SSK_WORKSPACE`): `validate`, `build_status` (one JSON list per collection, plus the approvals queue), `funnel_stats`, `build_review`, `build_queue_xlsx` (Chrome/Edge detection, labels in en/vi/es, avatar from `rep_name`), `compose_images` (JSON spec), `config_sync` (page JSON documents to TOML and back, including a facts document), `control_sync` (approval marks, pause flags, run requests, notes), `setup_workspace` (prerequisites, init, schedule conversion).
- **Control center** (`page/control-center.html`, built from `control-center.src.html` and `i18n/{en,vi,es}.json`): Setup wizard (8 steps), Channels, Approvals (Facebook-style preview, meaning in the UI language, Approve/Edit/Drop), Dashboard (overview, conversations, leads, posts, runs and scans, health), Control (pause all or per channel, run-now requests, schedule, notes). Light and dark, usable at 400px, no external scripts, shared data is rendered as text only.
- **Trust model** is enforced in code where it can be: marks and run requests are only reported, notes asking for outward actions are flagged for a chat confirmation, notes asking to weaken a safety rule are flagged as conflicting, and only documents the owner edited on the page (`_updated` newer than `_synced`) overwrite workspace config.
- **Skills**: `seeding-setup`, `sync-control`, `publish-status`, `daily-run`, `hot-replies`, `check-replies`, `post-approved`, `health-check`, `biweekly-report`. The Drive sync of the original project is not carried over (the page replaces it).
- **Docs** in English, Vietnamese and Spanish, `INSTALL.md`, `CHANGELOG.md`.

## What was tested, and how
- `python -m pytest -q`: **68 passed** (about 30 s).
  - `test_scripts.py`: validator rules (categories, funnel types and URL prefixes, fanpage URLs, undeclared languages), `build_status` collections, `funnel_stats`, xlsx labels, image composer, and the `config_sync` round trip (export, apply, TOML equal, validate; page edit, TOML, validate, status; presets; dry run; string escaping; facts).
  - `test_plugin.py`: no leftover client strings (`Thai Binh|Hải|Havana|MIRIKO|SUCHEL|eagodi|PmmX1q|Cuba`, Cuba allowed only in the es-419 style example), agent and skill front matter, referenced scripts and skills exist, `control_sync` (marks, stale marks, pause, requests, notes flags, skipped documents).
  - `test_setup.py`: prerequisites report, `init` of a fresh "Demo Co" workspace validates and is a git repo, schedule conversion between Vietnam and Madrid, and a draft-only first day (one test group, `queue.json`, `review.html`, `queue.xlsx`, dashboard collections).
  - `test_page.py`: i18n keys complete and in sync across en/vi/es, built page up to date, then 14 scenarios in headless Chrome against a local stub of `window.claude` (db and user): rendering in 3 languages, approval marks written and cleared, setup save and validation errors, channel paste and save, category add reconciling funnel and channels, facts, pause, run request and note, read-only viewer unable to write, dashboard sections, markup in shared data shown as text, and a page-to-TOML-to-validate-to-dashboard round trip.
- Screenshots of every tab at 1280px in en, vi and es (rendered with the stub and demo data) were read and fixed; a dark-mode check of Approvals; a script measured no horizontal overflow at 400px on every tab.
- `python scripts/validate.py` on `demo/`: 0 errors (5 warnings that are intended: draft knowledge, no tracking URL, no control-center URL).
- Isolation: nothing was written to `D:/Claude Projects/tb-social-seeding`. Its `git status` shows only `status/status.json` modified, which was already modified when this session started (the live session).

## What differs from the brief
- **No Thai Binh fixtures.** Copying TB `runs/`, `conversations/` and `leads.csv` into `fixtures/` was blocked by the permission classifier (real names and numbers), and I did not work around it. All tests use the synthetic "Demo Co" workspace made by `tools/make_demo.py`. As a result, "the same counts as today's TB dashboard" was not checked. `fixtures/` is git-ignored and empty.
- **Page testing** used headless Chrome (found first by `find_browser`) instead of Edge; the browser path logic accepts both.
- The page keeps `_updated` / `_synced` bookkeeping fields on config documents so a stale page copy cannot overwrite newer workspace edits.

## What remains
1. **Publish a real control-center artifact** ("SSK test" or a real brand): `/seeding-setup` step 3 has the exact call (`db` with admin-only writes, `user`). The first real publish should be checked once: the `ArtifactData` reads and writes the skills describe, the read-only viewer view, and that `${CLAUDE_PLUGIN_ROOT}` is expanded inside skill text as assumed.
2. **Install the plugin in Claude Code** (`/plugin marketplace add <path>`) and run `/seeding-setup` end to end on a real account. The marketplace and plugin manifests are minimal and untested against a live install.
3. **Live Facebook behaviour** of the agents (scan, draft, post) was not exercised: this session ran without a browser or Facebook. The agent prompts keep the selector notes from the original project, which should be re-checked.
4. **GitHub**: create the repository, push, and share the marketplace URL (needs the owner's account and an explicit OK). Add a LICENSE then; `plugin.json` says UNLICENSED for now.
5. **Thai Binh migration** (phase 6): turn the TB project into a workspace, move its facts and playbooks, import conversations and leads, retire the old dashboard after parity, with the owner's OK.
6. **Language reviews**: the es-419 and vi style guides are starting points; each language still needs its reviewer entry in `caps.toml`. The vi and es UI strings were written by Claude and should get a native read.
7. Smaller follow-ups: a keywords editor on the page (keywords are written at setup but not editable there yet), per-channel language of the approval sheet, and a `LICENSE`.
