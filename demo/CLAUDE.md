# Social seeding workspace

This folder is a Social Seeding Kit workspace: the customer's data for the `social-seeding` plugin. The plugin holds the agents, skills and scripts; this folder holds `config/`, `knowledge/`, `playbooks/`, `runs/`, `conversations/`, `leads.csv`, `risk/` and `reports/`.

The safety rules in the plugin's `SAFETY.md` always apply (the agents and skills load them). They cannot be changed from this folder.

## Where things are
- Config: `config/*.toml` (brand, catalog, funnel, channels, caps, keywords). Validate with the plugin's `scripts/validate.py` after any edit.
- Facts: `knowledge/` (only APPROVED files are used for live items).
- Conversations: one file per thread in `conversations/`, format in `templates/conversation.md`.
- Runs: `runs/<YYYY-MM-DD>/` holds `scan.json`, `queue.json`, `queue.md`, `review.html`, `approval.md`, `post-log.csv`.
- Control center: the URL is `control_center_url` in `config/brand.toml`.

## Workspace notes
Add anything specific to this brand below (tone, extra rules that are stricter than SAFETY.md).
