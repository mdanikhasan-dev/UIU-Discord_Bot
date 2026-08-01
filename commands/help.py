"""A compact, navigable command guide instead of a command dump."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR, BOT_NAME


TOPICS = {
    "home": (
        "What would you like to do?",
        (
            "**Plan a trimester**\n"
            "Open `/cgpa calculator` and add courses with dropdowns.\n\n"
            "**Check university updates**\n"
            "Use `/notices` for the public notice board or `/calendar` for verified dates.\n\n"
            "**Work with text**\n"
            "Use `/summary` with pasted text or a file.\n\n"
            "**Run a server activity**\n"
            "Use `/poll` to create a reaction poll."
        ),
    ),
    "cgpa": (
        "CGPA calculator",
        (
            "Run `/cgpa calculator`. The calculator opens privately.\n\n"
            "1. Use **Set standing** if you want a cumulative projection.\n"
            "2. Choose **Add course** for a new course or **Add retake** to replace "
            "an earlier grade.\n"
            "3. Select the credits and expected grade. Retakes also ask for the "
            "previous grade.\n"
            "4. Add the rest of your courses, then choose **Calculate CGPA**.\n\n"
            "Nothing entered in the calculator is saved."
        ),
    ),
    "updates": (
        "Notices and calendar",
        (
            "`/notices` shows the latest three links from UIU's public notice board.\n\n"
            "`/calendar` shows the verified current undergraduate calendar snapshot and "
            "links to UIU's authoritative page.\n\n"
            "Administrators can use `/setup` to choose an automatic notice channel and "
            "`/stop_notices` to disable delivery."
        ),
    ),
    "tools": (
        "Everyday tools",
        (
            "`/summary` privately condenses pasted text or a UTF-8 text file.\n\n"
            "`/poll` creates a reaction poll with 2–10 unique choices.\n\n"
            "`/ping` checks Discord gateway latency.\n\n"
            "`/about` explains the bot's version, privacy boundaries, and invite permissions."
        ),
    ),
    "admin": (
        "Administrator setup",
        (
            "`/setup #channel` sends future UIU notices to the selected channel.\n\n"
            "`/stop_notices` turns automatic delivery off without deleting the server's "
            "seen-notice history.\n\n"
            "The bot needs View Channel, Send Messages, Embed Links, Add Reactions, and "
            "Read Message History in the configured channel."
        ),
    ),
}


def help_embed(topic: str, avatar_url: str | None) -> discord.Embed:
    title, description = TOPICS.get(topic, TOPICS["home"])
    embed = discord.Embed(
        title=BOT_NAME if topic == "home" else title,
        description=description,
        color=BOT_ACCENT_COLOR,
    )
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Choose a guide below · this panel is visible only to you")
    return embed


class HelpTopicSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose a guide",
            row=0,
            options=[
                discord.SelectOption(
                    label="CGPA calculator",
                    description="Credits, grades, retakes, and projections",
                    value="cgpa",
                ),
                discord.SelectOption(
                    label="Notices and calendar",
                    description="University updates and automatic delivery",
                    value="updates",
                ),
                discord.SelectOption(
                    label="Everyday tools",
                    description="Summary, polls, latency, and bot details",
                    value="tools",
                ),
                discord.SelectOption(
                    label="Administrator setup",
                    description="Configure the automatic notice channel",
                    value="admin",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, HelpView)
        await interaction.response.edit_message(
            embed=help_embed(self.values[0], self.view.avatar_url), view=self.view
        )


class HelpView(discord.ui.View):
    def __init__(self, user_id: int, avatar_url: str | None) -> None:
        super().__init__(timeout=600)
        self.user_id = user_id
        self.avatar_url = avatar_url
        self.add_item(HelpTopicSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.user_id:
            return True
        await interaction.response.send_message(
            "Open your own guide with `/help`.", ephemeral=True
        )
        return False

    @discord.ui.button(label="Home", style=discord.ButtonStyle.secondary, row=1)
    async def home(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(
            embed=help_embed("home", self.avatar_url), view=self
        )

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.secondary, row=1)
    async def dismiss(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()


class Help(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="help", description="Open a private guide to UIU Bot")
    async def help_command(self, interaction: discord.Interaction) -> None:
        avatar_url = (
            str(self.client.user.display_avatar.url) if self.client.user else None
        )
        await interaction.response.send_message(
            embed=help_embed("home", avatar_url),
            view=HelpView(interaction.user.id, avatar_url),
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Help(client))
