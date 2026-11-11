---
name: health-check
description: Run the risk-manager's read-only account health check for the owner's profile (and the brand Page when enabled) and report GREEN/AMBER/RED with evidence.
---

# /health-check
1. Run the `risk-manager` agent, Job 1, for every enabled identity in `config/caps.toml`.
2. Show the owner:
   - the rating and the evidence lines;
   - any incident logged;
   - the caps in force today (halved if AMBER, paused if RED).
3. If RED: give the date the pause ends (`red_pause_hours`), and say what the owner should check themselves, such as Account Status or Support Inbox. Never attempt any recovery step in the account.
4. Run `/publish-status` so the control center's Health tab shows the new rating.
