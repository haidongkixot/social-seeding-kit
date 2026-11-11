---
name: hot-replies
description: Afternoon pass for social seeding. Reads the latest posts of every active group again, checks live conversations (stage 1+) for new replies, drafts next turns and replies to fresh buyer posts, reviews and risk-gates them, and sends a small queue for approval. Posts nothing.
---

# /hot-replies

`/check-replies` handles new comments and replies every hour. This skill's main job is the afternoon rescan of the latest posts for fresh buyer posts: on the busiest boards the latest 50 posts cover only a few hours, so buyer posts from the day would otherwise be missed. The time is `[schedule] hot_replies` in `config/caps.toml`.

The same pipeline as `/daily-run`, with two differences: **no health check** (it ran in the morning) and **no offer posts** (they are morning-only). The plugin's `SAFETY.md` applies.

1. `DATE` = today. Write the outputs with a `-pm` suffix: `scan-pm.json`, `moves-pm.json`, `drafts-pm.json`, `queue-pm.json`, `review-pm.html`. If the workspace is paused on the control center, stop.
2. Run `scout` exactly as in the morning (`[scan]` in `config/caps.toml`). Threads already in `scan.json` from the morning or in `conversations/` are not added twice.
3. Run `conversation-manager` on conversations with stage 1-3, plus new seeds from `scan-pm.json` (buyer posts and distributor discussions only, score >= 2). No `offer_post` moves.
4. Run `context-writer`, then `reviewer`, then `risk-manager` Job 2. The caps count everything already posted today.
5. Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/build_review.py" runs/<DATE> --suffix -pm` and send `review-pm.html` to the owner. Run `/publish-status` so the queue shows on the control center. Build the optional Excel sheet as in `/daily-run` step 8 (`approve-pm.json`).
6. If there are no new replies and no new buyer posts, tell the owner in one line (with posts read per group) and stop.
