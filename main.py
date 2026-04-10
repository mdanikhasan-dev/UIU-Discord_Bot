import asyncio
import os
import sys

import discord
from discord.ext import commands

from config.settings import BOT_NAME, BOT_VERSION, TOKEN


# ─────────────────────────────────────────────────────────────────────────────
# Intents
# ─────────────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
# NOTE: Using Intents.all() was the original approach; it works but requires
# the "Message Content" privileged intent to be enabled in the Dev Portal.
# If you get permission errors, switch back to: intents = discord.Intents.all()


# ─────────────────────────────────────────────────────────────────────────────
# Extension loader — skips invalid module names and logs failures cleanly
# ─────────────────────────────────────────────────────────────────────────────
async def load_extensions(client: commands.Bot) -> None:
    commands_dir = "commands"
    print("Loading extensions...")

    for filename in os.listdir(f"./{commands_dir}"):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue

        module_name = filename[:-3]

        # Skip files whose names are not valid Python identifiers
        # (e.g. "func(1)_for(string).py" cannot be imported).
        # These will still be present in the folder; they just will not
        # be loaded as Discord extensions.
        if not module_name.replace("_", "").isalnum():
            print(f"  - Skipped {filename} (not a valid module name)")
            continue

        try:
            await client.load_extension(f"{commands_dir}.{module_name}")
            print(f"  - Loaded {filename}")
        except commands.ExtensionAlreadyLoaded:
            print(f"  - Already loaded {filename}, skipping")
        except Exception as e:
            print(f"  - Failed to load {filename}: {type(e).__name__}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Bot class
# ─────────────────────────────────────────────────────────────────────────────
class UIUBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)
        # Prevents syncing on every reconnect within the same process lifetime.
        self.synced_once: bool = False

    async def setup_hook(self) -> None:
        """Called once when the bot first connects.  Load cogs and sync tree."""
        await load_extensions(self)

        # Only sync commands once per process start, not on every reconnect.
        # Repeated syncs across many restarts can hit Discord rate limits.
        if not self.synced_once:
            try:
                synced = await self.tree.sync()
                self.synced_once = True
                print(f"Synced {len(synced)} slash command(s).")
            except discord.HTTPException as e:
                print(f"Failed to sync commands (HTTP {e.status}): {e.text}")
            except Exception as e:
                print(f"Failed to sync commands: {e}")

    async def on_ready(self) -> None:
        """Fired on every successful (re)connection to Discord."""
        print(f"\nReady! Logged in as {self.user} (id={self.user.id})")
        print("-" * 45)
        # Do NOT do heavy work here — on_ready can fire multiple times on
        # reconnect.  Heavy startup work belongs in setup_hook (runs once).

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        import traceback
        print(f"Unhandled error in event '{event_method}':")
        traceback.print_exc()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
client = UIUBot()


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN is not set. Check your .env file.")
        sys.exit(1)

    print(f"{BOT_NAME} v{BOT_VERSION} is starting...")
    try:
        client.run(TOKEN, log_handler=None)
    except discord.LoginFailure:
        print("ERROR: Discord login failed — invalid token.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
