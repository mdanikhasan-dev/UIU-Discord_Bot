"""Validated reaction polls with two to ten choices."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR

POLL_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


class Poll(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="poll", description="Create a reaction poll with 2–10 options")
    @app_commands.describe(
        question="Question (maximum 200 characters)",
        option1="First option",
        option2="Second option",
        option3="Optional third option",
        option4="Optional fourth option",
        option5="Optional fifth option",
        option6="Optional sixth option",
        option7="Optional seventh option",
        option8="Optional eighth option",
        option9="Optional ninth option",
        option10="Optional tenth option",
    )
    @app_commands.checks.cooldown(2, 30.0, key=lambda i: i.user.id)
    async def create_poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str | None = None,
        option4: str | None = None,
        option5: str | None = None,
        option6: str | None = None,
        option7: str | None = None,
        option8: str | None = None,
        option9: str | None = None,
        option10: str | None = None,
    ) -> None:
        clean_question = question.strip()
        options = [
            option.strip()
            for option in (
                option1, option2, option3, option4, option5,
                option6, option7, option8, option9, option10,
            )
            if option and option.strip()
        ]
        if not clean_question or len(clean_question) > 200:
            await interaction.response.send_message(
                "The poll question must be 1–200 characters.", ephemeral=True
            )
            return
        if any(len(option) > 100 for option in options):
            await interaction.response.send_message(
                "Each poll option must be 100 characters or fewer.", ephemeral=True
            )
            return
        if len({option.casefold() for option in options}) != len(options):
            await interaction.response.send_message(
                "Poll options must be unique.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        option_lines = [
            f"{POLL_EMOJIS[index]}  {discord.utils.escape_mentions(option)}"
            for index, option in enumerate(options)
        ]
        embed = discord.Embed(
            title=discord.utils.escape_mentions(clean_question),
            description="\n\n".join(option_lines),
            color=BOT_ACCENT_COLOR,
        )
        embed.set_footer(text=f"Started by {interaction.user.display_name}")
        message = await interaction.followup.send(
            embed=embed,
            wait=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        for emoji in POLL_EMOJIS[: len(options)]:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                break


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Poll(client))
