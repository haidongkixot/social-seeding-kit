---
name: daily-run
description: Morning run for social seeding. Control-center sync, health check, scan, conversation update, drafting, review and risk gate, ending with a numbered queue sent to the owner for approval. Posts nothing. Use "/daily-run" or "/daily-run --draft-only".
---

# /daily-run

Run the steps **in order**, from the workspace folder. Browser steps share the owner's single browser (Claude in Chrome), so never run two browser agents at the same time. Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`. The plugin's `SAFETY.md` applies throughout.

`--draft-only`, or any day when `[languages]` for a used language has `native_review_done = false`, means:
- DRAFT knowledge is allowed;
- every item is marked `"draft_only": true`;
- the queue can't be posted.

## Steps
0. **Sync the control center:** run `/sync-control`, which reads the page's config edits, approval marks, pause flags and notes. If the page or its database is unavailable, say so and continue with the workspace files. A paused workspace (`control/state` has `paused = true`) stops here: tell the owner it is paused.
1. **Set up the run.**
   - `DATE` = today, in YYYY-MM-DD.
   - Create `runs/<DATE>/`.
   - Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py"`. If it fails, stop and show the errors.
2. **Health check:** run the `risk-manager` agent, Job 1. If **any identity is RED**, stop: write a note to `runs/<DATE>/queue.md` and alert the owner.
3. **Scan:** run the `scout` agent, which writes `scan.json`. Skip channels the control center has paused.
4. **Conversation update:** run the `conversation-manager` agent, which writes `moves.json` and updates `conversations/`.
5. **Drafts:** run the `context-writer` agent, which writes `drafts.json`. There are no browser actions here, so this step can start as soon as step 4 is done.
6. **Review:** run the `reviewer` agent, which marks PASS, FIX or DROP.
7. **Risk gate:** run the `risk-manager` agent, Job 2, which writes `queue.json`.
8. **Build the review files.**
   - Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_review.py" runs/<DATE>`, which writes `queue.md` and `review.html`. Send `review.html` to the owner with `SendUserFile`.
   - **Approvals on the control center:** run `/publish-status` so today's queue appears in the page's Approvals tab (preview, meaning in `ui_language`, Approve / Edit / Drop).
   - **Optional Excel sheet with pictures:** write `runs/<DATE>/approve.json` (per item `n, channel, group, url, type, category, activity, text, meaning, time`, plus a top-level `checks`) and run `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_queue_xlsx.py" runs/<DATE>/approve.json`. If the owner uses Google Drive, it can be uploaded as a Google Sheet; the owner marks Approve, Edit or Drop there, then confirms in chat.
   - Caption: "<N> items for today: <a> replies, <b> new seeds, <c> invites, <d> offer posts. Health: <GREEN/AMBER>. Reply 'approve 1-5, 8; edit 3: ...; drop 6', or mark them on the control center and say 'approved as marked'."
9. **Publish status:** run `/publish-status` to refresh the control center's dashboard data.
10. **Stop and wait for the owner's reply.** Posting happens only in `/post-approved`.

## Final message to the owner
- the health status;
- the funnel snapshot: open conversations by stage;
- the queue summary;
- any unreadable channels, for example "not a member yet: please join A2".
