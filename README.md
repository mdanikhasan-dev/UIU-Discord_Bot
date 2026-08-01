<p align="center">
  <img src="./Asset/readme/uiu-bot-command-center.webp" alt="UIU Bot project overview supplied by the maintainer" width="100%" />
</p>

<h1 align="center">UIU Bot</h1>

<p align="center">
  A Discord utility for UIU notices, academic planning, and the small server tasks that should not require another website.
</p>

<p align="center">
  <a href="#cgpa-calculator">CGPA calculator</a> ·
  <a href="#notices-that-arrive-in-order">Notice delivery</a> ·
  <a href="#the-command-desk">Commands</a> ·
  <a href="#run-it">Setup</a>
</p>

> The opening board is the original visual supplied by the maintainer. Some dates and interface examples inside that artwork are historical; the live behavior documented below is current.

UIU Bot is independent software. It is not an official United International University service, does not sign in to UCAM, and never asks for a student password.

## CGPA calculator

The calculator is a private Discord session, not a CSV parser or a wall of slash-command options.

```text
/cgpa calculator
       │
       ├── Add course  → credits → expected grade
       ├── Add retake  → credits → new grade → previous grade
       ├── Set standing → completed credits → current CGPA
       └── Calculate CGPA
```

The panel keeps regular courses and retakes separate, shows each course in its own readable block, and calculates both the trimester GPA and projected cumulative CGPA. Retakes replace the previous course quality points without adding the course credits twice.

The calculation uses UIU's [published grading scale](https://www.uiu.ac.bd/academics/grading-performance-evaluation/). UIU's public [academic policy](https://www.uiu.ac.bd/academics/academic-information-policies/) does not document every internal UCAM replacement rule, so UCAM remains the authoritative result.

Nothing entered in the calculator is written to disk.

## Notices that arrive in order

An administrator chooses a channel once with `/setup`. From there the bot checks UIU's public notice board every five minutes, compares each link with that server's local history, and posts only unseen notices.

```text
UIU public notice board
          ↓
brief shared cache
          ↓
server-specific seen history
          ↓
configured Discord channel
```

Notices are delivered oldest-first when several appear together. A link is recorded only after Discord accepts the message, so a failed send is not silently treated as delivered.

## The command desk

| Need | Command | What appears in Discord |
| --- | --- | --- |
| Plan a trimester | `/cgpa calculator` | Private interactive credit, grade, and retake controls |
| Read current notices | `/notices` | The latest three links from UIU's public board |
| Check academic dates | `/calendar` | Verified undergraduate dates with the official source |
| Condense text | `/summary` | A private cleaned brief or summary |
| Start a vote | `/poll` | A validated reaction poll with 2–10 options |
| Find a feature | `/help` | A private topic-based guide instead of a command dump |
| Check the bot | `/ping` | Online status and Discord gateway latency |
| Configure delivery | `/setup #channel` | Administrator-only notice-channel setup |
| Stop delivery | `/stop_notices` | Administrator-only delivery shutdown |

### Summary privacy

`/summary` processes text locally unless `use_ai` is explicitly set to `true`. Local input stays inside the bot process. The AI option sends that request to Groq and is unavailable until the owner supplies `GROQ_API_KEY`. UIU Bot does not save summary input or output.

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

Add the Discord token to `.env`, then start the process:

```powershell
python main.py
```

The default `.env.example` also documents the optional Groq model, log level, command-sync switch, notice interval, state path, and seen-notice limit. Secrets belong only in `.env`; that file is ignored by Git.

## Runtime boundaries

- `data/notices_memory.json` contains live Discord server/channel state and is ignored by Git.
- Grade entries and summary text exist only for the duration of their private interaction.
- The current calendar is a verified Summer 2026 undergraduate snapshot, not a UCAM feed.
- Local JSON state supports one bot process. Multi-instance hosting needs shared transactional storage.
- The bot must remain running on a connected machine or hosting service to stay online.

<details>
<summary><strong>Repository map and checks</strong></summary>

```text
commands/   Discord commands and interactive views
config/     Validated environment and runtime settings
services/   CGPA math, summarization, and atomic notice state
utils/      Public UIU notice fetching and calendar data
tests/      Synthetic tests without student or server data
main.py     Startup, logging, extension loading, and command sync
```

```powershell
python -m compileall -q main.py commands config services utils tests
python -m unittest discover -s tests -v
```

GitHub Actions runs the same compilation and test suite on Python 3.12 and 3.13.

</details>

---

<p align="center">
  Built for UIU Discord communities. Maintained independently.
</p>
