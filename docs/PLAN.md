# Plan: "Social Seeding Kit", a portable Claude Code plugin with a control-center artifact

## Context
`D:\Claude Projects\tb-social-seeding` works for Thai Binh. It has:
- 6 agents (scout, conversation-manager, context-writer, reviewer, risk-manager, reporter);
- 8 skills;
- Python scripts;
- a dashboard artifact.

It is all built for one client:
- 122 hard-coded brand, place and URL references;
- the categories fmcg and construction;
- the Havana timezone, es-419 and vi;
- the Edge path, Drive IDs and the artifact URL.

Hải wants to package it so **another Claude account can deploy it for its own groups and fanpages**, with an **HTML artifact to set up, control and monitor** the system.

Decisions:
- **Package:** a Claude Code plugin (GitHub marketplace).
- **The page is the center:** configuration, approval marking, pause/resume and the dashboard all live there. Posting, joining and DMs still need a confirmation in chat.
- **Thai Binh becomes the first install.**
- **UI languages:** English, Vietnamese and Spanish.

## Shape of the package
A new repo `D:\Claude Projects\social-seeding-kit` (git). It is a plugin marketplace with one plugin, `social-seeding`:
```
.claude-plugin/marketplace.json
plugins/social-seeding/
  .claude-plugin/plugin.json
  SAFETY.md                      fixed hard rules (from tb CLAUDE.md rules 1-8), not configurable
  agents/                        6 agents, generalized (brand, languages, categories, endpoints from config)
  skills/  seeding-setup, sync-control, daily-run, hot-replies, check-replies, post-approved,
           health-check, publish-status, biweekly-report, (optional) sync-drive
  scripts/ common.py, validate.py, build_review.py, build_queue_xlsx.py, build_status.py,
           funnel_stats.py, compose_images.py, config_sync.py (new)
  templates/workspace/           skeleton copied by setup: config/*.toml, knowledge/*, playbooks/*,
                                 templates/conversation.md, CLAUDE.md (workspace notes + import of SAFETY.md)
  templates/playbooks/           sales-promo, partner-recruitment (generic, with {placeholders})
  templates/styles/              language style guides: es-419 (from playbooks/es-419-style.md), vi, en
  page/control-center.html       the artifact page (i18n en/vi/es)
  i18n/{en,vi,es}.json           UI strings
docs/ README.en.md / README.vi.md / README.es.md, INSTALL, CHANGELOG
```

**Plugin vs. workspace.**
- The plugin holds the logic: agents, skills, scripts and the page.
- A **workspace folder** holds the customer's data: `config/`, `knowledge/`, `playbooks/`, `runs/`, `conversations/`, `leads.csv`, `risk/`, `reports/`.
- Scripts take the workspace from the current directory.
- Updating the plugin never touches customer data.

## Generalization (from the inventory)
**New config.** Everything client-specific moves into config, validated by `validate.py`:
- `config/brand.toml`:
  - `brand_name`, `rep_name`, `disclosure` (e.g. "Soy {rep}, de {brand}");
  - `owner_email`;
  - `ui_language` (en|vi|es);
  - `audience_timezone`, `operator_timezone`.
- `config/catalog.toml`: categories (`id`, label, keywords). Replaces the fixed fmcg/construction sets in `validate.py:21,72,140`, `funnel_stats.py:102` and `build_status.py:214`.
- `config/funnel.toml`: one end-of-funnel destination per category. Types are `whatsapp|telegram|zalo|messenger|website`, each with a URL and optional `tracked_base`. Replaces `whatsapp.toml` and the `chat.whatsapp.com`-only check (`validate.py:77`).
- `config/channels.toml`:
  - The same schema as now.
  - `url` accepts `facebook.com/groups/…` and fanpages (`facebook.com/<page>`).
  - New `kind = "page"`.
- `config/caps.toml`, `keywords.toml`, `languages`: the same keys as now.
  - Languages are open: any BCP-47 code with its own native-review flag.
  - Keyword groups are keyed by category.

**Code changes.**
- **Agents and skills:**
  - Replace "Thai Binh", "Hải", Havana, es-419 and E1–E2 with config lookups.
  - Keep the generic Facebook DOM notes from `scout.md` 4b and the funnel stages.
- **Scripts:**
  - `build_queue_xlsx.py`: detect Chrome or Edge instead of the hard-coded `EDGE` path (`:19`); take column labels from the UI language; take the avatar letter from `rep_name`.
  - `build_status.py`: drop the artifact URL (`:5`) and the TB-specific readiness checks (`:166-194`). Readiness comes from config (knowledge approved, language reviewed, funnel set, channels joined).
  - `compose_post_images.py` → `compose_images.py`: keep the generic `top_and_strip` and `two_stacked`, and take inputs from a JSON spec.
- **Safety rules:** they move to `SAFETY.md` and stay unchanged. The page cannot edit them.

## Control center artifact (`page/control-center.html`)
- A custom HTML artifact with the `db` and `user` capabilities. Load the `artifact-capabilities` and `artifact-design` skills before writing it.
- Setup publishes one per workspace and stores its URL in `config/brand.toml`.
- **Store rules:** writes are admin (owner) only; viewers can read.

**Tabs:**
1. **Setup wizard:**
   - brand and representative;
   - categories;
   - funnel destinations;
   - languages;
   - knowledge facts, written as short approved statements;
   - channels list (paste URLs);
   - caps preset (careful / normal);
   - schedule.
2. **Channels:** state, wave, `promo_posts` and links flags.
3. **Approvals:** today's queue with a preview picture, Spanish/Vietnamese/English meaning, and Approve / Edit / Drop. This replaces the Google Sheet; the sheet stays optional.
4. **Dashboard:** today's dashboard sections (KPIs, funnel, conversations, leads with WhatsApp numbers, posts, runs, scans, health, incidents).
5. **Control:**
   - pause/resume all, or one channel;
   - "run now" requests;
   - schedule hours;
   - a notes box for Claude.

**Data flow:**
- Claude writes the status documents into the artifact's database with `ArtifactData` batch. This replaces the single `status.json` blob, and `build_status.py` emits per-collection JSON.
- The page writes `config/*`, `approvals/<date>/*` and `control/*`.

**Trust model (unchanged rules):**
- The new `sync-control` skill reads the page's documents into the workspace TOML (`config_sync.py`), just like `/sync-drive` today.
  - Config edits apply.
  - Approvals marked on the page and "run now" are acted on only after the owner confirms in chat ("approved as marked").
  - Joins, posts and DMs are never triggered by page data alone.
  - Notes are treated as the owner's input, but checked against `SAFETY.md`.

## `/seeding-setup` (first run in a new account)
1. Check prerequisites:
   - Claude in Chrome connected;
   - the Facebook tab signed in (the owner signs in; Claude never does);
   - Gmail and Drive connectors (optional);
   - Python with openpyxl and Pillow.
2. Create the workspace from `templates/workspace/`, then `git init`. Keep `runs/`, `conversations/`, `leads.csv` and `reports/` git-ignored.
3. Publish the control center. The owner fills the wizard, or answers in chat. Run `sync-control`, then `validate.py`.
4. Optional: research channels, the same as the current Phase 0 research, with the owner choosing.
5. Offer schedules:
   - `CronCreate` session jobs for daily-run, hot-replies and check-replies, timed from `audience_timezone`;
   - or durable scheduled tasks if the account allows them.
6. First day in draft-only mode. Same as now.

## How the build runs: a separate session, low token use (Hải, 2026-11-12)
- **A separate session** does all package work. It is started with `start_session`, with its own folder `D:\Claude Projects\social-seeding-kit` (created first, `git init`), and named "Social Seeding Kit build".
  - This seeding session keeps running `/check-replies`, approvals and posting, untouched.
- **Isolation rules** for the build session:
  - It may only **read** `tb-social-seeding`, as the source of copies, and never writes there.
  - It never uses Claude in Chrome or Edge: the browser and the Facebook account belong to the live seeding.
  - It never touches the TB dashboard artifact, the Drive folder or Gmail.
  - Testing uses a demo workspace with fixture data (fake posts, conversations and leads), not Facebook.
  - The only artifact it may publish is a **test** control-center artifact, named "SSK test".
- **Local compute first, to save tokens:**
  - Copy and generalize files with Python and PowerShell scripts: copytree plus scripted string and regex replacement driven by a mapping table. Don't read and retype files through the model.
  - Check with local tools only: `validate.py`, a small pytest suite for the scripts, `grep` for leftover TB strings, and headless Edge/Chrome (`--screenshot`) to render the control-center page and xlsx previews.
  - Read files in parts with `grep`; avoid whole-file reads.
  - **Model:** the session runs on Sonnet. Mechanical subagents (moving files, i18n string tables) use Haiku. Only the page design and the agent prompt rewrites use the session model.
  - No web research and no browsing; everything needed is already in the TB project.
- The build session reports back at the end of each phase with a one-line summary. Hải reviews in that session.

## Thai Binh migration (later, after the package is done)
Not part of this build (Hải, 2026-11-12). It is kept here as the follow-up.
- Install the plugin locally from `social-seeding-kit` (`/plugin marketplace add <path>`).
- Turn `tb-social-seeding` into a workspace:
  - **Moves into config files:** the TB data (brand Thai Binh Corp / Hải; categories fmcg and construction; funnel = the 2 WhatsApp groups; timezones America/Havana and Asia/Ho_Chi_Minh; languages es-419 and vi).
  - **Stays as workspace content:** the TB playbooks (`cuba-partnership`, the objection scripts) and the es-419 style.
  - **Removed:** the project-level agents and skills, once parity is checked, so the plugin's versions are used.
- Publish a new TB control center, and import the existing conversations, leads and post logs. Retire the old dashboard artifact after parity, and only with Hải's OK.

## Distribution
- Version 0.1.0 in a local git repo.
- Pushing to GitHub (private or public) and sharing the marketplace URL needs Hải's GitHub account and explicit OK. That is outward-facing, so it is asked at that step.
- The README in 3 languages covers: install, setup, the daily routine, safety rules, and what the owner must do themselves (join groups, sign in, enable email notifications).

## Phases (each ends with a check)
1. Create the repo skeleton and move scripts in with config-driven generalization. `validate.py` passes on the TB workspace.
2. Generalize the agents and skills, and write `SAFETY.md`. A TB `/daily-run --draft-only` gives the same shape of outputs as today.
3. Build the control center page, `sync-control` and `config_sync.py`. A round trip works: page edit → TOML → validate → dashboard.
4. Build `/seeding-setup` and test it on a fresh demo workspace ("Demo Co", one test group, draft-only).
5. Write the docs in en/vi/es, tag v0.1.0, and ask before any GitHub push.
6. (Later, separately) migrate Thai Binh.

## Verification
- **Demo workspace:**
  - Install the plugin into an empty folder and run `/seeding-setup` with a made-up brand and one Facebook group the owner joined.
  - `validate.py` gives 0 errors.
  - The control center opens, and the wizard values appear in `config/*.toml` after `sync-control`.
  - `/daily-run --draft-only` produces `queue.json`, `approve.xlsx` and dashboard data.
- **Thai Binh fixtures** (no live Facebook):
  - A copy of TB's `runs/`, `conversations/` and `leads.csv` in the demo workspace builds the same counts as today's dashboard.
  - An approval marked on the test page is acted on only after "approved as marked" in chat.
- **Isolation:** `git status` in `tb-social-seeding` shows no changes made by the build session.
- **Safety:**
  - A page note asking to post or join triggers nothing without a chat confirmation.
  - A grep for "Thai Binh|Hải|Havana|MIRIKO|eagodi" in `plugins/social-seeding/` returns nothing.
