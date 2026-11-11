---
name: check-replies
description: Hourly check for new comments, replies and Messenger messages from people engaging with our posts. Reads Facebook notification emails in Gmail first (if the connector is set up), and falls back to a single read of facebook.com/notifications. Drafts replies for approval and alerts the owner. Never posts. Use "/check-replies" or the hourly scheduled run.
---

# /check-replies

Goal: know about new activity without browsing Facebook. **Read-only on Facebook. Nothing is sent without the owner's approval in chat (SAFETY.md rule 2).** If the workspace is paused on the control center, stop. Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`.

## 1. Gmail first (optional)
Skip to step 2 if the Gmail connector is not available.
- Search with the Gmail connector `search_threads`:
  `from:facebookmail.com newer_than:1d`
  (view `THREAD_VIEW_SUMMARY`, pageSize 50).
- **Read only Facebook notification emails.** Never open other mail.
- Skip any Gmail message id already in `runs/replies-state.json` under `gmail_ids`.
- For each new email, read it with `get_thread` and keep only those about:
  - a comment on one of **our** posts (post ids in `runs/*/post-log.csv`);
  - a reply to one of our comments;
  - a tag of the owner by a person in `conversations/`;
  - a Messenger message from a person in `conversations/`.
- From each email take: the person's display name, their text (verbatim, as far as the email shows it), the group, and the post/comment link (`/posts/<id>`, `comment_id`).

## 2. Fallback: one page of Facebook
Use it if no facebookmail notification arrived in the last 2 hours while conversations are open, if the Gmail connector is unavailable, or if an email lacks the comment text.
- In the owner's browser (Claude in Chrome), read **facebook.com/notifications only**. Keep only the rows about our posts and comments.
- Open a single post permalink only when you need the verbatim text. Reuse the patterns in the scout agent, section 5: comments are `[role="article"][aria-label^="Comment by"]`; replies are `aria-label^="Reply by"`; wait about 4 seconds for comments to load.
- **Messenger:** open facebook.com/messages only for threads from people in `conversations/`. Never read other chats.
- Stop on any login page, checkpoint or warning.

## 3. Dedupe and match
- `runs/replies-state.json` holds `{"gmail_ids":[], "comment_ids":[], "last_email_at":"", "last_check":""}`. Add every handled id there.
- Match each item to `conversations/*.md` by post id and person.
  - A new person on one of our posts opens a new conversation at stage 1.
  - Anything unrelated to our posts is ignored.
- Add each turn verbatim to the conversation's Turns table. Reset `unanswered_turns` to 0, and move the stage per the conversation's playbook.

## 4. When something is new
1. Run `conversation-manager` on the changed conversations, including the **group-reply tags** rule (0 to `max_extra_tags` extra tags).
2. Then run `context-writer`, `reviewer` and `risk-manager` Job 2.
3. Messenger messages get the `dm_inbound` move from the playbook.
   - **Contacts a person gives us themselves** (for example a phone number): tell the owner in chat and add it to `leads.csv` (column `contact`). It goes nowhere else except the control center's leads table, via `/publish-status` (SAFETY.md rule 8). The conversation file notes "shared contact, <date>".
4. Write `runs/<date>/approve-<HHMM>.json` (same format as `/daily-run` step 8; use type "Reply", "Group reply" or "Messenger reply").
5. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_queue_xlsx.py" runs/<date>/approve-<HHMM>.json` if the owner uses the Excel sheet, and run `/publish-status` so the drafts appear in the control center's Approvals tab.
6. Alert the owner with `PushNotification`, short and in `ui_language`. Example: "B1: Caridad replied 'yes'. 2 replies waiting for approval."
7. Also send a short chat message: the new turns verbatim, the drafts, and "approve ...".

## 5. When nothing is new
No alert. Add one line to `runs/<date>/replies-log.md`: time, source (gmail or fallback), and "0 new".

## 6. Always
Update `last_check` in the state file. Run `/publish-status` only when something changed.
