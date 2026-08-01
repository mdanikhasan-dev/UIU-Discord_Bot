"""Bot identity, privacy boundaries, and least-privilege invite link."""

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_DESCRIPTION, BOT_NAME, BOT_OWNER, BOT_VERSION


class About(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="about", description="Show bot details and privacy boundaries")
    async def about_command(self, interaction: discord.Interaction) -> None:
        permissions = discord.Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            add_reactions=True,
            read_message_history=True,
        )
        invite_link = None
        if self.client.user:
            invite_link = discord.utils.oauth_url(
                self.client.user.id,
                permissions=permissions,
                scopes=("bot", "applications.commands"),
            )
        embed = discord.Embed(
            title=f"{BOT_NAME} · v{BOT_VERSION}",
            description=BOT_DESCRIPTION,
        )
        if self.client.user:
            embed.set_thumbnail(url=str(self.client.user.display_avatar.url))
        embed.add_field(name="Maintainer", value=BOT_OWNER)
        embed.add_field(name="Affiliation", value="Independent; not an official UIU service")
        embed.add_field(
            name="Privacy",
            value=(
                "The bot does not request UCAM credentials. Grade and summary inputs are "
                "processed in memory and are not stored by the bot. Selecting `/summary`'s "
                "AI engine sends that input to the configured provider."
            ),
            inline=False,
        )
        if invite_link:
            embed.add_field(
                name="Invite",
                value=f"[Add {BOT_NAME} with only its required permissions]({invite_link})",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(About(client))
