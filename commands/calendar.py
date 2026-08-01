"""Current official UIU undergraduate academic-calendar command."""

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR
from utils.fetch_calendar import fetch_academic_calendar


class Calendar(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="calendar",
        description="Show verified dates from the current UIU undergraduate calendar",
    )
    async def academic_calendar(self, interaction: discord.Interaction) -> None:
        calendar = await fetch_academic_calendar()
        lines = [
            f"**{event['date']}** — {event['description']}"
            for event in calendar["events"]
        ]
        embed = discord.Embed(
            title=calendar["semester_title"],
            description="\n".join(lines),
            url=calendar["source_url"],
            color=BOT_ACCENT_COLOR,
        )
        embed.add_field(
            name="Official calendar",
            value=f"[Open the full calendar and footnotes]({calendar['source_url']})",
            inline=False,
        )
        embed.set_footer(
            text=f"Snapshot verified {calendar['verified_on']}. UIU's page is authoritative."
        )
        await interaction.response.send_message(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Calendar(client))
