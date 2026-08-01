import os
import sys

from dotenv import load_dotenv

load_dotenv()

TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# Bot metadata
BOT_NAME: str = "UIU_BOT"
BOT_VERSION: str = "1.0.2"
BOT_OWNER: str = "sawlper"
BOT_DESCRIPTION: str = "Your own soft place for notices, updates, and community info."

# ─ Notice loop settings
# How often the notice-checking background loop runs, in minutes.
# Do NOT set below 5 — it puts unnecessary load on the UIU website and
# dramatically increases the chance of the bot's IP being blocked.
NOTICE_CHECK_INTERVAL_MINUTES: int = 5

# Maximum number of seen notice URLs to keep per server.
# Keeps the JSON file from growing without bound after many months.
MAX_SEEN_NOTICES: int = 200
