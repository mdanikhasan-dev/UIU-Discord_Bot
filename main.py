"""UIU Bot process entry point."""

from __future__ import annotations

import logging
import sys

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_NAME, BOT_VERSION, EXTENSIONS, LOG_LEVEL, SYNC_COMMANDS, TOKEN


logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("discord.ext.commands.bot").setLevel(logging.ERROR)
logger = logging.getLogger("uiu_bot")


intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True


class UIUBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        failures: list[str] = []
        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                logger.info("Loaded %s", extension)
            except Exception:
                failures.append(extension)
                logger.exception("Failed to load %s", extension)
        if failures:
            raise RuntimeError("Required extensions failed: " + ", ".join(failures))

        if SYNC_COMMANDS:
            try:
                synced = await self.tree.sync()
                logger.info("Synced %d application command(s)", len(synced))
            except discord.HTTPException:
                logger.exception("Discord application-command sync failed")

    async def on_ready(self) -> None:
        logger.info("%s v%s is online as %s", BOT_NAME, BOT_VERSION, self.user)

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        logger.exception("Unhandled Discord event error in %s", event_method)


client = UIUBot()


@client.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    original = getattr(error, "original", error)
    if isinstance(original, app_commands.CommandOnCooldown):
        message = f"That command is cooling down. Try again in {original.retry_after:.1f}s."
    elif isinstance(original, app_commands.MissingPermissions):
        message = "You do not have permission to use that command."
    else:
        logger.error(
            "Unhandled application-command error: %s",
            type(original).__name__,
            exc_info=(type(original), original, original.__traceback__),
        )
        message = "The command could not be completed. The error was logged without your input."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


def main() -> int:
    if not TOKEN:
        logger.error("DISCORD_TOKEN is not set. Add it to the local .env file.")
        return 1
    logger.info("Starting %s v%s", BOT_NAME, BOT_VERSION)
    try:
        client.run(TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("Discord rejected the configured token")
        return 1
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    return 0


if __name__ == "__main__":
    sys.exit(main())
