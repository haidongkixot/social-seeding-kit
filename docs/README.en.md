# Social Seeding Kit

A Claude Code plugin that helps one person seed their brand in Facebook groups and fanpages without breaking the rules of the groups or of Facebook. Claude finds fitting threads, drafts replies that suit each conversation, checks them against your approved facts, and puts a numbered queue in front of you. **You approve every item. Claude posts nothing on its own.**

A web page (the control center) is where you set the system up, mark approvals, pause it and watch results.

Languages of the page and of these docs: English, Tiếng Việt ([README.vi.md](README.vi.md)), Español ([README.es.md](README.es.md)).

## What you get
- **Scout**: reads the latest posts of your active groups (read-only) and scores threads.
- **Conversation manager**: follows each conversation from first reply to an invitation (Seed, Engaged, Qualified, Invited, Joined).
- **Writer, reviewer, risk manager**: drafts, checks facts and tone, and holds the day's queue to daily caps, pacing and warm-up. A health check rates your account GREEN, AMBER or RED.
- **Control center** (a page published from Claude): Setup, Channels, Approvals, Dashboard, Control.
- **Reports** every two weeks, with data-backed suggestions.

## Install
Step-by-step guide: [GUIDE.en.md](GUIDE.en.md) / [GUIDE.vi.md](GUIDE.vi.md). See also [INSTALL.md](INSTALL.md). In short:
```
/plugin marketplace add <path-or-github-repo>
/plugin install social-seeding@social-seeding-kit
```
Then in an empty folder, start Claude Code and run `/social-seeding:seeding-setup`.

## Set up (once per brand)
1. `/seeding-setup` checks the tools, asks a few questions, and creates your **workspace** folder (config, facts, playbooks, runs, conversations). Your data lives there; updating the plugin never touches it.
2. It publishes the **control center**. Open its **Setup** tab: brand and representative, categories, funnel destinations (a WhatsApp group, Telegram, Zalo, Messenger or a website per category), languages, facts, channels, limits and schedule.
3. Run `/sync-control`. Your edits are written into the workspace and validated.
4. Day one is **draft-only**: you see drafts, nothing can be posted.

## The daily routine
| When | Command | What happens |
|---|---|---|
| Morning | `/daily-run` | Health check, scan, drafts, review and risk gate. The queue appears on the Approvals tab. |
| After you look | mark on the page, then tell Claude "approved as marked", or reply "approve 1-5; edit 3: ...; drop 6" | Claude shows what you approved and `/post-approved` posts only that, paced, with the right identity. |
| Afternoon | `/hot-replies` | A second look for new buyer posts. |
| Hourly | `/check-replies` | New comments and messages, from Facebook notification emails when Gmail is connected. Drafts replies and alerts you. |
| Any time | `/health-check`, `/sync-control`, `/publish-status` | Account health, apply page edits, refresh the dashboard. |
| Every 2nd Friday | `/biweekly-report` | Funnel, quality, risk and channel report. |

## Safety rules (fixed)
They are in `plugins/social-seeding/SAFETY.md` and cannot be changed from config, the page or chat.
1. Real, disclosed identity only: your profile, with the brand role stated. No fake personas.
2. Nothing is posted without your approval in chat. Marks on the page are proposals.
3. Claude never signs in, never handles 2FA or CAPTCHAs, and joins groups only when you ask.
4. Only compliant behaviour: caps, pacing, relevance, warm-up. No evasion.
5. Facts come only from approved knowledge files.
6. No cold DMs.
7. On wholesale boards: reply only to buyer posts, at most one offer post a day, links only after warm-up.
8. No personal data beyond people who engaged with you and a contact they gave you themselves.

## What you must do yourself
- Sign in to Facebook in the browser Claude in Chrome uses, and stay signed in.
- Join the groups and fanpages yourself, one wave at a time, then set each channel to Active with the date you joined.
- Review each language before live use (someone fluent, or you).
- Approve facts: tick them on the page.
- Enter the member count of each funnel destination every week (joins are measured from it).
- Optional: connect Gmail and turn on Facebook notification emails.

## Folder layout
```
plugins/social-seeding/   the plugin: agents, skills, scripts, page, templates, SAFETY.md
workspace/ (yours)        config/*.toml, knowledge/, playbooks/, runs/, conversations/, leads.csv, risk/, reports/
```
Config files: `brand.toml`, `catalog.toml`, `funnel.toml`, `channels.toml`, `caps.toml` (with `[languages]`), `keywords.toml`. `python scripts/validate.py` checks all of them.
