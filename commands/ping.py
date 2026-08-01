"""Discord gateway latency command."""

import discord
from discord import app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="ping", description="Check Discord gateway latency")
    async def ping_command(self, interaction: discord.Interaction) -> None:
        latency_ms = max(0, round(self.client.latency * 1000))
        await interaction.response.send_message(
            f"Discord gateway latency: **{latency_ms} ms**",
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Ping(client))
