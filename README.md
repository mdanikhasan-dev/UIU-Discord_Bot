# UIU Bot

UIU Bot keeps a Discord server close to the public information students check most often: university notices, current academic dates, and grade calculations. It also includes private text summarization and practical server utilities.

It is an independent project, not an official United International University service. It never asks for a UCAM login or password.

## Commands

### Academic tools

| Command | What it does |
| --- | --- |
| `/cgpa calculator` | Opens a private interactive calculator with credit and grade dropdowns, retake support, and optional cumulative projection. |
| `/calendar` | Shows the current verified undergraduate academic-calendar snapshot with the official source. |

The calculator follows UIU's [published grading scale](https://www.uiu.ac.bd/academics/grading-performance-evaluation/). No formatted rows or files are required:

1. Run `/cgpa calculator`.
2. Add current completed credits and CGPA when a cumulative projection is needed.
3. Select **Add course**, then choose credits and a grade.
4. For a retake, select **Add retake**, then choose the credits, new grade, and previous grade.
5. Add the remaining courses and select **Calculate**.

The session is ephemeral and is not written to the bot's files. Retake projections replace the previous course quality points without adding its credits twice. UIU's public [retake policy](https://www.uiu.ac.bd/academics/academic-information-policies/) does not document every UCAM implementation detail, so UCAM remains authoritative.

### Summaries

`/summary` accepts pasted text or a UTF-8 `.txt`, `.md`, or `.csv` attachment. The private local engine is the default. Already-short text is cleaned for readability instead of being returned as a fake summary.

- `use_ai: false` keeps the text inside the bot process.
- `use_ai: true` explicitly sends the text to the configured Groq API and is unavailable until the owner sets `GROQ_API_KEY`.
- The bot processes input in memory and does not write the input or result to its files or logs.

### Notices and server utilities

| Command | Access | What it does |
| --- | --- | --- |
| `/notices` | Everyone | Returns the latest three links from UIU's public notice board. |
| `/poll` | Everyone | Creates a validated reaction poll with two to ten unique options. |
| `/ping` | Everyone | Reports Discord gateway latency. |
| `/help` | Everyone | Opens a private, navigable guide organized by task. |
| `/about` | Everyone | Shows the version, privacy boundaries, and a least-privilege invite link. |
| `/setup #channel` | Administrator | Selects a channel for automatic notice delivery. |
| `/stop_notices` | Administrator | Disables automatic notice delivery for that server. |

The notice reader caches the public page briefly, checks automatically every five minutes, sends unseen links oldest-first, and records a link only after Discord accepts the message.

## Run it

Python 3.12 or newer is recommended.

```powershell
git clone https://github.com/mdanikhasan-me/UIU-Discord_Bot.git
cd UIU-Discord_Bot
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add the Discord bot token to `.env`, then start the process:

```powershell
python main.py
```

The bot must run on a connected machine or hosting service to stay online. `SYNC_COMMANDS=true` publishes the slash-command schema at startup; it can be disabled after a stable deployment.

## Runtime data

Automatic notice settings live in `data/notices_memory.json`. The file can contain Discord server and channel identifiers, so Git ignores it. Writes are schema-validated, locked within the process, flushed to disk, and atomically replaced. `data/notices_memory.example.json` documents the empty structure without real identifiers.

No grade rows, summary inputs, or summary outputs are stored by the application.

## Project map

```text
commands/   Discord command cogs and the notice-delivery loop
config/     Validated environment and runtime settings
services/   Grade math, summarization, and atomic notice state
utils/      Public UIU notice fetching and calendar data
tests/      Synthetic unit tests; no student or server data
main.py     Startup, logging, extension loading, and command sync
```

## Checks

```powershell
python -m compileall -q main.py commands config services utils tests
python -m unittest discover -s tests -v
```

GitHub Actions runs both checks on Python 3.12 and 3.13. The repository is a long-running Python service; it does not deploy the source tree to GitHub Pages.

## Operational limits

- The calendar is a verified Summer 2026 undergraduate snapshot, not a live UCAM feed. UIU's linked page is authoritative.
- Notice parsing depends on the structure of UIU's public website and can require maintenance when that page changes.
- Local JSON state is suitable for one bot process. Multi-instance hosting should replace it with transactional shared storage.
- The Groq free-plan limits and model availability are controlled by Groq and may change.
