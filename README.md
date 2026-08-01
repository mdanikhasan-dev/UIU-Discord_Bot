# UIU Bot

UIU Bot keeps a Discord server close to the public information students check most often: university notices, current academic dates, and grade calculations. It also includes private text summarization and practical server utilities.

It is an independent project, not an official United International University service. It never asks for a UCAM login or password.

## Commands

### Academic tools

| Command | What it does |
| --- | --- |
| `/grade scale` | Shows UIU's official marks, letter grades, and grade points. |
| `/grade marks` | Converts a percentage mark to the corresponding UIU grade. |
| `/grade calculate` | Reads typed rows or a text/CSV file and calculates term GPAs, attempted and earned credits, and a portal-compatible CGPA estimate. |
| `/grade project` | Projects a CGPA after a planned number of credits. |
| `/grade target` | Calculates the GPA needed across planned credits to reach a target CGPA. |
| `/grade template` | Downloads a synthetic CSV example with the accepted columns. |
| `/calendar` | Shows the current verified undergraduate academic-calendar snapshot with the official source. |

The grade calculator follows UIU's [published grading scale](https://www.uiu.ac.bd/academics/grading-performance-evaluation/). It excludes `W` and `I`, includes `F` in attempted credits, and treats the latest graded row for a repeated course code as the effective attempt. UIU's public [retake policy](https://www.uiu.ac.bd/academics/academic-information-policies/) does not document every UCAM replacement detail, so the result is deliberately labelled an estimate. UCAM remains authoritative.

Accepted grade rows are:

```text
term,course,credits,grade
261,CSE 1001,3,A-
261,ENG 1001,3,B+
```

`course,credits,grade` is also accepted. Files may be UTF-8 `.csv`, `.tsv`, or `.txt`; rows copied from the seven-column UCAM results table are understood as well. Running courses are skipped.

### Summaries

`/summary` accepts pasted text or a UTF-8 `.txt`, `.md`, or `.csv` attachment.

- `Private · processed locally` is the default. It uses an extractive summarizer inside the bot process and makes no external request.
- `AI · sends text to Groq` is opt-in. The choice itself is explicit consent to send that command's text to the configured Groq API. If Groq is temporarily unavailable, the command clearly labels its local fallback.
- The bot processes input in memory and does not write the input or result to its files or logs.

The AI option is unavailable until the bot owner sets `GROQ_API_KEY`. The private engine always works without an AI key.

### Notices and server utilities

| Command | Access | What it does |
| --- | --- | --- |
| `/notices` | Everyone | Returns the latest three links from UIU's public notice board. |
| `/poll` | Everyone | Creates a validated reaction poll with two to ten unique options. |
| `/ping` | Everyone | Reports Discord gateway latency. |
| `/help` | Everyone | Opens a private command directory. |
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
