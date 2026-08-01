"""A compact health response for Discord gateway latency."""

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR, BOT_NAME


class Ping(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="ping", description="Check whether UIU Bot is online")
    async def ping_command(self, interaction: discord.Interaction) -> None:
        latency_ms = max(0, round(self.client.latency * 1000))
        embed = discord.Embed(
            title=f"{BOT_NAME} is online",
            description=f"Discord gateway latency · **{latency_ms} ms**",
            color=BOT_ACCENT_COLOR,
        )
        if self.client.user:
            embed.set_thumbnail(url=str(self.client.user.display_avatar.url))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Ping(client))
