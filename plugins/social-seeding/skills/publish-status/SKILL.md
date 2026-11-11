---
name: publish-status
description: Refresh the control center's dashboard data from the workspace files. Runs at the end of /daily-run, /hot-replies, /check-replies and /post-approved, or on "update the status page".
---

# /publish-status

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`. The plugin's `SAFETY.md` applies (leads hold only what rule 8 allows).

1. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_status.py"` from the workspace. It writes one JSON list per collection to `status/` (`summary`, `groups`, `runs`, `scans`, `rejected`, `conversations`, `queue`, `funnel`, `posts`, `health`, `incidents`, `readiness`, `knowledge`, `memberCounts`, `links`, `leads`) and `status/index.json`.
2. Also run `python "${CLAUDE_PLUGIN_ROOT}/scripts/config_sync.py" export --out status/config`, so the page's Setup tab starts from the current config (documents `brand`, `catalog`, `funnel`, `channels`, `caps`, `keywords`, `languages`).
3. Write the documents to the artifact database with `ArtifactData` (load it with ToolSearch), using the URL in `control_center_url` of `config/brand.toml`. If the URL is empty, run `/seeding-setup` first; if the tool is unavailable, stop and say so.
   - One `batch` call per collection (or a few), each write a `set` of the document with its `id`.
   - Config documents go to the `config` collection. **Do not overwrite a config document the owner edited on the page since the last sync:** if `ArtifactData` `get` shows a newer `_updated` than your export, run `/sync-control` first.
   - For a collection that shrinks (for example `queue` after a new day), `delete` the documents that are no longer in the new list. Never delete `approvals`, `notes`, `runRequests` or `control`: those belong to the page.
4. Do not write anything outside the artifact's database. Say in one line what was published (collection counts from `status/index.json`).
