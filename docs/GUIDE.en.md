# Social Seeding Kit: install and user guide

This guide takes you from an empty computer to a working daily routine. Allow about an hour for the first setup. Vietnamese: [GUIDE.vi.md](GUIDE.vi.md).

**The one rule to remember:** Claude drafts, you decide. Nothing is posted, no group is joined and no one is messaged unless you approve it in the Claude Code chat.

---

## Part 1. Before you start

You need:

| What | Why | How to check |
|---|---|---|
| Claude Code (CLI or desktop app) | Runs the kit | `claude --version` |
| Claude in Chrome extension, connected | Claude reads Facebook in your browser | Claude Code lists it under connected browsers |
| A Facebook account, signed in, that is a member of your groups | The identity that writes | Open facebook.com in that browser |
| Python 3.11 or newer | The kit's scripts | `python --version` |
| `pip install openpyxl Pillow tzdata` | Approval sheets, images, time zones | `python -c "import openpyxl, PIL, zoneinfo"` |
| git | Your workspace is a git folder | `git --version` |
| Chrome or Edge | Preview pictures in the approval sheet | Usually already installed |
| Access to the private repo `haidongkixot/social-seeding-kit` | To install the plugin | Ask the owner to invite your GitHub account |
| Optional: Gmail connector | Cheaper hourly reply checks | Turn on Facebook notification emails too |

---

## Part 2. Install the plugin

### 2.1 Make a workspace folder
One folder per brand, for example `D:\Seeding\acme`. Keep it empty for now.

### 2.2 Add the marketplace and install
Open a terminal **inside that folder** and run:

```
claude plugin marketplace add haidongkixot/social-seeding-kit
claude plugin install social-seeding@social-seeding-kit --scope local
```

(From a local copy instead of GitHub: `claude plugin marketplace add "D:\path\to\social-seeding-kit"`.)

**Why `--scope local`:** the plugin then loads only in this folder. If you install it for your whole user account and another project has its own skills named `daily-run` or `scout`, the names collide.

Check it worked:
```
claude plugin details social-seeding@social-seeding-kit
```
You should see 9 skills and 6 agents.

### 2.3 Check the prerequisites
```
python "<plugin folder>\scripts\setup_workspace.py" prereqs
```
Every line should say `"ok": true`. Fix any that don't (usually a `pip install`). `/seeding-setup` also runs this check for you.

---

## Part 3. First setup (once per brand)

Start Claude Code in your workspace folder and type:

```
/social-seeding:seeding-setup
```

Claude walks you through 7 steps:

1. **Prerequisites.** It checks the tools and asks you to confirm you are signed in to Facebook.
2. **Workspace.** It asks in one message for:
   - brand name and representative name (the real person whose profile writes);
   - owner email;
   - your interface language: `en`, `vi` or `es`;
   - your time zone and your audience's time zone, for example `Asia/Ho_Chi_Minh` and `Europe/Madrid`;
   - the languages used in the groups, for example `en`, `vi`, `es-419`;
   - your categories, for example `home=Home goods`.

   It then creates the folders, playbooks and style guides, and makes the folder a git repository.
3. **Control center.** It publishes your private control-center page and saves its link in `config/brand.toml`.
4. **Configuration.** You fill in the page's Setup tab (Part 4), then Claude runs `/sync-control` to apply it.
5. **Channel research** (optional). Claude searches public pages for candidate groups. You choose which ones to use.
6. **Schedules** (optional). Claude offers recurring runs and creates each one only after you say yes.
7. **Draft-only first day.** Everything is a marked draft until your facts and languages are approved.

---

## Part 4. The control center

Open the link Claude gave you, or see `control_center_url` in `config/brand.toml`. The page is private: only you, and Editors you invite, can change things. People you share it with as viewers can only read.

### Setup tab (8 steps)
| Step | What to fill in | Tip |
|---|---|---|
| Brand and representative | Names, email, disclosure sentence, time zones | The disclosure, for example "I am {rep}, from {brand}.", opens every first message |
| Categories | One row per product line or partner theme, with keywords | Each category gets its own funnel destination |
| Funnel destinations | Per category: WhatsApp group, Telegram, Zalo, Messenger or website link | WhatsApp links must start `https://chat.whatsapp.com/`. Enter member counts every week |
| Languages | Language codes, and tick **Reviewed** once someone fluent has checked the style | Unreviewed languages produce drafts only |
| Facts | Short true statements, ticked **Approved** | The only facts Claude may use. No prices or stock unless you write them here |
| Channels | Paste group or fanpage URLs, one per line | Then join them yourself (Part 5) |
| Limits | **Careful** for the first 2 weeks, then **Normal** | Safety rules apply whatever you pick |
| Schedule | Daily run, afternoon pass, reply-check hours | In your computer's time zone |

Press **Save** on each step. Then, in Claude Code, say `/sync-control`. Claude writes your edits into the workspace, validates them and tells you about any problems. The header shows "Config synced" when it worked.

### Channels tab
One row per group or fanpage. Keep these right:
- **State**:
  - *Not joined*: you haven't joined yet.
  - *Active*: joined, and **Joined on** is set.
  - *Cooling down*: rested after a removal.
  - *Retired*: no longer used.
- **Own offer posts** and **Links in comments**: what the group's rules allow. *Unknown* is treated as *No*.
- **Kind**: *Discussion*, *Ad board* (high-volume buying and selling) or *Fanpage*.

### Approvals tab
The day's queue. For each item you see a Facebook-style preview, the meaning in your language, and why Claude proposes it.
- Press **Approve**, **Edit** (write what should change) or **Drop**.
- Then tell Claude in chat: **"approved as marked"**.
- Claude lists what you marked and asks you to confirm. Only then does it post.

### Dashboard tab
- **Overview**: active channels, open conversations, items posted, leads, the funnel, and a readiness checklist.
- **Conversations**: each person's stage, from Seed to Joined.
- **Leads**: people who engaged, with a contact only if they gave it to you themselves.
- **Posts**, **Runs and scans**, **Health** (GREEN, AMBER or RED per day, plus incidents).

### Control tab
- **Pause everything** / **Resume**: all runs and posting stop while paused.
- **Pause single channels**: that group is skipped.
- **Ask Claude to run something now**: leaves a request. Claude asks you in chat before running it.
- **Notes for Claude**: preferences and questions. A note can never make Claude post or join on its own, or change a safety rule.

---

## Part 5. Things only you can do

1. **Sign in to Facebook** in the browser Claude in Chrome uses, and stay signed in. Claude never signs in, types passwords or solves CAPTCHAs.
2. **Join the groups.** Do it one wave at a time, a few groups per week. Then set each channel to **Active** with the date you joined. Warm-up counts from that date: helpful comments only, no links, no offer posts for 14 days on the Careful preset.
3. **Approve facts and languages** on the Setup tab.
4. **Enter member counts** of each funnel destination every week. This is how joins are measured.
5. **Approve in chat** every day.

---

## Part 6. The daily routine

| When | You type | What happens |
|---|---|---|
| Morning (default 08:00) | `/social-seeding:daily-run` | Sync, account health check, scan of active groups, drafts, review and risk gate. The queue appears on the Approvals tab |
| Once you have looked | Mark on the page and say **"approved as marked"**, or type `approve 1-5, 8; edit 3: shorter; drop 6` | Claude repeats what will be posted. After your yes, `/post-approved` posts it, spaced at least 10 minutes apart, and logs every link |
| Afternoon (default 16:00) | `/social-seeding:hot-replies` | A second scan for new buyer posts and replies |
| Hourly in the evening, if set up | `/social-seeding:check-replies` | New comments and messages are drafted and you get an alert. Nothing is sent |
| Any time | `/social-seeding:health-check` | Account health with evidence |
| After editing the page | `/social-seeding:sync-control` | Applies the edits and reports notes and requests |
| Every second Friday | `/social-seeding:biweekly-report` | Funnel, quality, risk and channel report with suggestions |

You can usually leave out the `social-seeding:` prefix when no other skill has the same name.

**Draft-only days:** add `--draft-only` to the daily run (for example `/social-seeding:daily-run --draft-only`). Nothing can be posted from that queue. Use it on day one, and whenever you want to see drafts without any risk.

### How to give approvals in chat
- `approve 1-6, 9`: post items 1 to 6 and 9.
- `edit 4: <new text>`: Claude uses your text exactly.
- `edit 4: make it shorter`: Claude rewrites it and shows you the new text first.
- `drop 7`: never posted.
- **"approved as marked"**: use the marks from the Approvals tab. Claude still lists them and waits for your yes.

---

## Part 7. Health and safety

Claude rates the account every morning:

| Rating | Meaning | What happens |
|---|---|---|
| GREEN | No warnings, posts visible | Normal limits |
| AMBER | A removal, a failed visibility check, or many pending posts | Limits halved, no links |
| RED | Any Facebook warning, restriction, checkpoint or feature block | Everything stops for 72 hours and you are alerted. **Check Account Status and Support Inbox yourself.** Claude never tries to recover the account |

The fixed safety rules (in `SAFETY.md`, which no setting can change):
1. Real, disclosed identity only.
2. Nothing posted without your approval in chat.
3. Claude never signs in, and joins groups only when you ask.
4. Compliant behaviour only: limits, pacing, relevance. No evasion.
5. Facts only from approved knowledge.
6. No cold private messages.
7. On ad boards: reply only to buyers, at most 1 offer post a day per group.
8. No personal data collection beyond people who engaged with you.

---

## Part 8. Troubleshooting

| You see | Do this |
|---|---|
| Page says "Waiting for Claude to publish the configuration" | Run `/social-seeding:publish-status` |
| Header says "Last sync failed" | Open the Control tab to read the errors, fix them on the Setup tab, then run `/sync-control` again. Claude restored your previous config, so nothing broke |
| `validate.py` errors | Each line names the file and the field. Fix it on the page or in `config/*.toml` |
| "No Chrome or Edge found" | Install one, or set `SSK_BROWSER` to the browser's .exe path |
| "cannot convert timezones" | `pip install tzdata` |
| Skill not found | Run Claude Code inside the workspace folder (local install), or check `claude plugin list` |
| Nothing gets posted | Is it a draft-only queue? Is a language unreviewed or a fact unapproved? Is the workspace paused? Is health RED? |
| A post went to "pending approval" | Normal in some groups. It counts against your limits; Claude logs it |
| Login page, CAPTCHA or "temporarily blocked" | Claude stops. Sort it out yourself in the browser, then run `/social-seeding:health-check` |

---

## Part 9. Updating and backing up

- **Update the plugin:** `claude plugin marketplace update social-seeding-kit`, then restart Claude Code. Your workspace data is never touched.
- **Back up:** the workspace is a git repository. Config and knowledge are tracked. Runs, conversations, leads, reports and risk logs are deliberately not tracked because they hold people's names, so copy those folders yourself if you need a backup.
- **Several brands:** one workspace folder and one control center per brand. Install the plugin with `--scope local` in each.
