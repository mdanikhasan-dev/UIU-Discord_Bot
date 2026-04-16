# UIU BOT

<p align="center">
  <strong>Your own soft place for notices, updates, and community info.</strong>
</p>

<p align="center">
  A clean, GitHub-ready Discord bot for United International University communities.
  <br />
  It brings together UIU notices, academic calendar info, server utilities, and quick admin setup in one place.
</p>

<p align="center">
  <a href="https://github.com/Sawlper/UIU-BOT-Discord/actions/workflows/static.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Sawlper/UIU-BOT-Discord/static.yml?branch=master&style=for-the-badge&label=github%20pages&color=2EA043" alt="GitHub Pages workflow" />
  </a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/discord.py-2.3%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="discord.py 2.3+" />
  <img src="https://img.shields.io/badge/status-active-ff6b6b?style=for-the-badge" alt="Project status active" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Sawlper/UIU-BOT-Discord?style=for-the-badge&color=F4B400" alt="GitHub stars" />
  <img src="https://img.shields.io/github/forks/Sawlper/UIU-BOT-Discord?style=for-the-badge&color=00BFA6" alt="GitHub forks" />
  <img src="https://img.shields.io/github/last-commit/Sawlper/UIU-BOT-Discord?style=for-the-badge&color=5C7CFA" alt="Last commit" />
  <img src="https://img.shields.io/github/repo-size/Sawlper/UIU-BOT-Discord?style=for-the-badge&color=8E44AD" alt="Repository size" />
</p>

## Why This Bot Is Useful

- Pulls the latest UIU notices directly into Discord.
- Posts new notices automatically to a channel you choose.
- Shows key academic calendar dates on demand.
- Includes quality-of-life commands like polls, help, ping, and about.
- Keeps server-specific notice memory so duplicate announcements are avoided.

## Preview

<p align="center">
  <img src="./Asset/CommandsPVWgifs/Screenshot 2025-11-10 022703.png" alt="UIU Bot preview screenshot" width="92%" />
</p>

<p align="center">
  <sub>Main Discord view with the bot in action.</sub>
</p>

<table>
  <tr>
    <td align="center" width="50%">
      <strong>Help Command Walkthrough</strong><br />
      <img src="./Asset/CommandsPVWgifs/bothelp.gif" alt="Help command preview" width="100%" />
    </td>
    <td align="center" width="50%">
      <strong>Notice Setup Walkthrough</strong><br />
      <img src="./Asset/CommandsPVWgifs/dcsetup.gif" alt="Setup command preview" width="100%" />
    </td>
  </tr>
</table>

## Features

| Area | What it does |
| --- | --- |
| UIU Notices | Fetches the latest notices from the UIU website and shows the top results in Discord. |
| Auto Notice Posting | Checks for new notices every 5 minutes and posts only unseen ones to configured channels. |
| Academic Calendar | Displays the current UIU academic calendar from maintained static data. |
| Server Tools | Includes admin setup for notice channels and stop controls for automatic notice posting. |
| Community Utilities | Provides poll creation, help, ping, and about commands. |

## Slash Commands

| Command | Access | Description |
| --- | --- | --- |
| `/help` | Everyone | Shows the full command list. |
| `/ping` | Everyone | Checks bot latency. |
| `/about` | Everyone | Displays bot info and invite details. |
| `/poll` | Everyone | Creates a poll with up to 10 options. |
| `/notices` | Everyone | Shows the latest 3 UIU notices. |
| `/calendar` | Everyone | Shows important academic calendar dates. |
| `/setup` | Admin | Sets the channel for automatic UIU notice posts. |
| `/stop_notices` | Admin | Disables automatic notice posting for the server. |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/Sawlper/UIU-BOT-Discord.git
cd UIU-BOT-Discord
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your environment variables

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_bot_token_here
```

### 5. Run the bot

```bash
python main.py
```

## Configuration

| File | Key | Purpose |
| --- | --- | --- |
| `config/settings.py` | `BOT_NAME` | Bot display name used in responses and startup logs. |
| `config/settings.py` | `BOT_VERSION` | Tracks the current bot version. |
| `config/settings.py` | `NOTICE_CHECK_INTERVAL_MINUTES` | Controls how often the bot checks for new notices. |
| `config/settings.py` | `MAX_SEEN_NOTICES` | Caps stored notice history per server. |
| `.env` | `DISCORD_TOKEN` | Discord bot token required to connect. |

> Notice checks intentionally run every 5 minutes to reduce load on the UIU website and lower the risk of IP blocks.

## Tech Stack

- Python
- `discord.py`
- `python-dotenv`
- `requests`
- `beautifulsoup4`

## Project Structure

```text
UIU-BOT-Discord/
|-- .github/
|   `-- workflows/
|       `-- static.yml
|-- .gitignore
|-- Asset/
|   |-- CommandsPVWgifs/
|   `-- Icon  gifs/
|-- commands/
|   |-- about.py
|   |-- calendar.py
|   |-- help.py
|   |-- notices.py
|   |-- ping.py
|   |-- poll.py
|   `-- setup.py
|-- config/
|   `-- settings.py
|-- data/
|   `-- notices_memory.json
|-- utils/
|   |-- fetch_calendar.py
|   `-- fetch_notices.py
|-- main.py
`-- requirements.txt
```

## Notes

- The bot uses slash commands and syncs them when the app starts.
- Notice scraping is wrapped safely so one failed fetch does not kill the background loop.
- Academic calendar data is currently static and should be updated manually each semester.
- The README preview assets come from `Asset/CommandsPVWgifs`, so GitHub visitors can see the bot before running it.

## GitHub Files Included

- `.github/workflows/static.yml` for GitHub Pages deployment workflow.
- `.gitignore` to keep secrets, cache files, and virtual environments out of the repo.
- `README.md` for project presentation, onboarding, and setup.

## Contributing

If you want to improve the bot, open an issue or submit a pull request with a clear description of the change. Small fixes, polish, and new commands are all welcome.
