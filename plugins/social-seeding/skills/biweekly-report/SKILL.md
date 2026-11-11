---
name: biweekly-report
description: Produce the bi-weekly seeding performance report with improvement suggestions (reporter agent). Use every second Friday or when the owner asks for a report.
---

# /biweekly-report
1. **Period:** the 14 days ending yesterday, unless the owner gives dates.
2. **Member counts:** ask the owner for this Friday's member count of each funnel destination if `config/funnel.toml` has no `[[member_count]]` entry within the last 3 days. Add the numbers as a new entry, one value per category id. (They can also enter them on the control center's Setup tab; run `/sync-control` to pick them up.)
3. **Report:** run the `reporter` agent, which writes `reports/<period>.md` and `.html`.
4. **Send** the HTML to the owner with `SendUserFile`. If the owner uses Google Drive, upload it there too when they ask.
5. **Summarise in chat:** the top 3 findings and the suggestions that need the owner's decision, such as retiring channels, raising caps or adding knowledge.
