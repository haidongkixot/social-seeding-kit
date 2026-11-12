---
name: seeding-setup
description: First-run setup of a social seeding workspace in a new Claude account. Checks prerequisites, creates the workspace folder from the plugin templates, publishes the control-center page, applies what the owner enters there, optionally researches channels, offers schedules, and starts in draft-only mode. Use "/seeding-setup" once per brand.
---

# /seeding-setup

You are setting up one brand's seeding workspace. The plugin's `SAFETY.md` (in `${CLAUDE_PLUGIN_ROOT}`) applies from the first minute. The owner is the person talking to you: they sign in to Facebook and join groups themselves. **You never sign in, join, post, comment or message anyone during setup.** Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`.

## Fast path (started by `setup.cmd` / `setup.sh`)
If the current folder already has `config/brand.toml`, the one-command installer (`bootstrap.py`) has already installed the Python packages, created this workspace and installed the plugin. Then:
1. Run the prerequisites check (step 1) but only report problems; do not ask the workspace questions of step 2.
2. Go straight to step 3 (publish the control center), then tell the owner in `ui_language`, in two or three lines: open the link, fill in the **Setup** tab step by step, press Save on each step, and say "done" here when finished.
3. Continue with step 4 when the owner says done, then steps 5-7 as usual.

## 1. Prerequisites
Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/setup_workspace.py" prereqs` and report in plain words what is missing.
- Python 3.11 or newer, `openpyxl`, `Pillow` (`pip install openpyxl Pillow`), `git`, and a Chrome or Edge browser (for approval-sheet previews). `tzdata` too on Windows (`pip install tzdata`).
- **Claude in Chrome** connected to the browser where the owner is signed in to Facebook. Ask the owner to check this themselves: open Facebook in that browser and make sure the account is signed in. If it isn't connected, setup can continue but scans can't run yet.
- Optional: the Gmail connector (Facebook notification emails make `/check-replies` cheaper) and the Google Drive connector.
Fix what you can, ask the owner for the rest, and continue once the required items pass.

## 2. Create the workspace
Ask in chat, short and one message: brand name, the representative's name (the real person whose profile will write), the owner's email, the language of the owner's interface (`en`, `vi` or `es`), where the audience lives (timezone), the owner's own timezone, the languages used in the groups (BCP-47 codes), and the categories (an id and a name each). Anything the owner is unsure about can be filled in later on the control center.

Then run, in a new, empty folder the owner names (default `./<brand-slug>-seeding`):
`python "${CLAUDE_PLUGIN_ROOT}/scripts/setup_workspace.py" init <folder> --brand ... --rep ... --language ... --audience-tz ... --operator-tz ... --owner-email ... --lang-codes ... --category id=Label ...`
It copies the templates, writes the answers into `config/`, adds the playbooks and style guides for the chosen languages, and runs `git init` (`runs/`, `conversations/`, `leads.csv`, `reports/`, `risk/` and `status/` stay out of git). Work from that folder from now on. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py"`: it should give 0 errors.

## 3. Publish the control center
1. Copy `${CLAUDE_PLUGIN_ROOT}/page/control-center.html` into the workspace as `status/control-center.html` (the Artifact tool publishes files from the working directory).
2. Load the `artifact-capabilities` skill, then publish it with the Artifact tool: `file_path` that copy, `icon` `dashboard`, `description` "Set up, approve and monitor social seeding for <brand>.", and
   `capabilities: {"db": {"rules": [{"path": "", "read": "view", "write": "admin"}]}, "user": {}}`.
   Writes are then limited to the owner (and Editors they invite); viewers can read. The page stays private until the owner shares it.
3. Put the URL in `control_center_url` of `config/brand.toml`.
4. Run `/publish-status` to seed the page's database (config, readiness and empty dashboard collections). Open the page for the owner.

## 4. Fill in the configuration
Tell the owner to open the page's **Setup** tab: brand, categories, funnel destinations, languages, facts, channels, limits, schedule. They can instead answer in chat and you write the files. Facts need the owner's approval (a tick on the page, or a "yes" in chat): never mark one approved yourself.

When the owner says they are done, run `/sync-control` (it applies the page's edits, runs `validate.py`, and reports problems). Fix validation errors with the owner. Run `/publish-status` so the page shows the result.

Reminders to give the owner:
- Join the Facebook groups yourself, one wave at a time, then set each channel's state to **Active** with the date you joined. Warm-up (no links, no offer posts) counts from that date.
- A language is used live only after someone fluent has reviewed it. Until then everything is a marked draft.
- Turn on Facebook notification emails if you use the Gmail connector.

## 5. Optional: research channels
If the owner has no group list, offer to research candidates with web search (public pages only, no logging in): groups and fanpages for each category and language, their size, activity and rules as far as public. Present a ranked list; the owner picks. Add the ones the owner picks to `config/channels.toml` with `state = "not_joined"`, then `/publish-status`. Joining remains the owner's own action.

## 6. Offer schedules
Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/setup_workspace.py" schedule` to get the daily run, afternoon pass and reply-check times as cron expressions in the owner's timezone, with what they mean in the audience's timezone. Offer:
- `CronCreate` session jobs for `/daily-run`, `/hot-replies` and `/check-replies` (they run while this Claude session is open);
- or durable scheduled tasks with the `/schedule` skill, if the owner's account allows them.
Create a job only after the owner says yes to that job. Scheduled jobs only draft and alert; they never post.

## 7. First day: draft-only
Explain, in a few lines, what happens next: `/daily-run --draft-only` scans the active channels, drafts replies and offer posts with marked **draft-only** status, and publishes the queue to the Approvals tab. Nothing can be posted on a draft-only day. After the owner has reviewed the drafts, and the knowledge and languages are approved, `/daily-run` without the flag produces a postable queue, and `/post-approved` posts only what the owner approves in chat.

Finish with a short summary: where the workspace is, the control center URL, what is still open (readiness list on the Dashboard tab), and the first command to run.
