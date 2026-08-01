"""Environment-backed configuration for UIU Bot."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


def _integer(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value < minimum or value > maximum:
        raise RuntimeError(f"{name} must be from {minimum} to {maximum}.")
    return value


TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
BOT_NAME = "UIU Bot"
BOT_VERSION = "2.0.0"
BOT_OWNER = "sawlper"
BOT_DESCRIPTION = "UIU notices, academic utilities, and community tools for Discord."
BOT_ACCENT_COLOR = 0xFF8A00

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SYNC_COMMANDS = os.getenv("SYNC_COMMANDS", "true").strip().lower() in {"1", "true", "yes"}

NOTICE_CHECK_INTERVAL_MINUTES = _integer(
    "NOTICE_CHECK_INTERVAL_MINUTES", 5, minimum=5, maximum=1440
)
MAX_SEEN_NOTICES = _integer("MAX_SEEN_NOTICES", 200, minimum=20, maximum=2000)
NOTICE_STATE_PATH = os.getenv("NOTICE_STATE_PATH", "data/notices_memory.json")

EXTENSIONS: tuple[str, ...] = (
    "commands.about",
    "commands.calendar",
    "commands.cgpa",
    "commands.help",
    "commands.notices",
    "commands.ping",
    "commands.poll",
    "commands.setup",
    "commands.summary",
)
