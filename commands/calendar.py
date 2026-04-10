from discord.ext import commands
from discord import app_commands
import discord

from utils.fetch_calendar import fetch_academic_calendar


class Calendar(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="calendar",
        description="Shows the current academic calendar's important dates.",
    )
    async def academic_calendar(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        calendar_data = await fetch_academic_calendar()

        if not calendar_data:
            await interaction.followup.send(
                "Error: The static calendar data is missing."
            )
            return

        embed = discord.Embed(
            title="📅 UIU Academic Calendar & Important Dates",
            description=f"Important dates for the **{calendar_data['semester_title']}**.",
            color=discord.Color.orange(),
        )

        for event in calendar_data["events"]:
            embed.add_field(
                name=f"🗓️ {event['date']}",
                value=event["description"],
                inline=False,
            )

        embed.set_footer(
            text=f"Last updated: {calendar_data['last_updated']} (Manually maintained)"
        )

        await interaction.followup.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Calendar(client))
