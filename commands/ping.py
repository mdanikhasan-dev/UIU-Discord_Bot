from discord.ext import commands
from discord import app_commands
import discord


class Ping(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="ping",
        description="Checks the bot's reaction speed (latency).",
    )
    async def ping_command(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.client.latency * 1000)
        await interaction.response.send_message(
            f"Pong! 🏓\nBot Latency: **{latency_ms} ms**"
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Ping(client))
