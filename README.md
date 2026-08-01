# UIU Bot

UIU Bot is a Discord utility for United International University communities. It checks the public UIU notice board, posts unseen notices to configured channels, exposes academic-calendar data, and provides a small set of server commands.

This repository contains the bot itself. It is not an official UIU service and does not log in to UCAM or collect student portal credentials.

## What the bot does

- Reads the latest notices from `https://www.uiu.ac.bd/notice/`.
- Returns the newest three notices with `/notices`.
- Checks for new notice links every five minutes.
- Keeps separate notice history for each configured Discord server.
- Posts unseen notices oldest-first so the channel stays chronological.
- Provides calendar, poll, latency, help, and setup commands.

## Commands

| Command | Access | Result |
| --- | --- | --- |
| `/notices` | Everyone | Shows the latest three UIU notices. |
| `/calendar` | Everyone | Shows the academic dates currently maintained by the project. |
| `/poll` | Everyone | Creates a reaction poll with two to ten options. |
| `/ping` | Everyone | Reports the bot's Discord latency. |
| `/about` | Everyone | Shows bot information and its invite link. |
| `/help` | Everyone | Opens a private command guide. |
| `/setup #channel` | Administrator | Selects the channel for automatic notice posts. |
| `/stop_notices` | Administrator | Stops automatic notice posts for that server. |

## How notice delivery works

1. An administrator runs `/setup` and chooses a text channel.
2. The bot checks the public UIU notice page every five minutes.
3. Each notice URL is compared with that server's local seen list.
4. Unseen notices are posted to the configured channel.
5. Successfully posted URLs are recorded so they are not sent again.

If the UIU website cannot be reached, the current check ends and the next scheduled check tries again.

## Run the bot

```powershell
git clone https://github.com/mdanikhasan-me/UIU-Discord_Bot.git
cd UIU-Discord_Bot

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` in the repository root:

```env
DISCORD_TOKEN=your_bot_token_here
```

Start the process:

```powershell
python main.py
```

The token must remain local. `.env` is ignored by Git and should never be included in screenshots, issues, or commits.

## Configuration

The main runtime values are in `config/settings.py`:

| Setting | Purpose |
| --- | --- |
| `BOT_NAME` | Display name used by the bot. |
| `BOT_VERSION` | Current application version. |
| `NOTICE_CHECK_INTERVAL_MINUTES` | Delay between automatic notice checks. |
| `MAX_SEEN_NOTICES` | Maximum stored notice URLs per server. |

Do not reduce the notice interval below five minutes. Repeatedly scraping the UIU site faster than necessary is not responsible or useful.

## Repository layout

```text
UIU-Discord_Bot/
├── commands/       Discord slash-command cogs
├── config/         Environment and runtime settings
├── data/           Local notice-delivery state
├── utils/          UIU notice and calendar fetchers
├── main.py         Bot startup and command loading
└── requirements.txt
```

## Current limitations

- Academic-calendar data is maintained manually and can become outdated.
- Notice parsing depends on the public UIU page structure.
- Runtime notice state is stored in JSON on the machine running the bot.
- The bot must stay running on a connected machine or hosting service to remain online.

Changes should be small enough to review, include a clear reason, and be tested before the live bot is restarted.
