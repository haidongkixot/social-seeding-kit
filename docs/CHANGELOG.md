# Changelog

## 0.1.0 (2026-11-12)
First packaged version, generalized from a single-client seeding project.

- Plugin `social-seeding` with six agents (scout, conversation-manager, context-writer, reviewer, risk-manager, reporter) and nine skills (`seeding-setup`, `sync-control`, `publish-status`, `daily-run`, `hot-replies`, `check-replies`, `post-approved`, `health-check`, `biweekly-report`).
- Fixed safety rules in `SAFETY.md`; they are not configurable.
- Config schema validated by `validate.py`: `brand.toml`, `catalog.toml`, `funnel.toml`, `channels.toml` (groups and fanpages), `caps.toml` (with open `[languages]`), `keywords.toml`.
- Control-center page (English, Vietnamese, Spanish): Setup wizard, Channels, Approvals, Dashboard, Control.
- `config_sync.py` (page documents to TOML and back) and `control_sync.py` (approval marks, pause flags, run requests, notes).
- Workspace templates, playbooks (sales-promo, partner-recruitment) and style guides (en, vi, es-419).
- Test suite for the scripts, the setup flow and the page (against a stubbed artifact runtime).

Not in this version: publishing a real control-center artifact, a GitHub release, and migrating the original project to the plugin.
