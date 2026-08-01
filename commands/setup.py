"""Administrator commands for automatic UIU notice delivery."""

import discord
from discord import app_commands
from discord.ext import commands

from services.notice_store import NoticeStoreError, notice_store


class Setup(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="setup",
        description="Set the channel for automatic UIU notice updates",
    )
    @app_commands.describe(channel="Channel that should receive new UIU notices")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild_id is not None
        try:
            await notice_store.configure(interaction.guild_id, channel.id)
        except NoticeStoreError:
            await interaction.followup.send(
                "Notice settings could not be saved safely. Check the bot logs before retrying.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            f"Automatic UIU notices will be posted in {channel.mention}.",
            ephemeral=True,
        )

    @app_commands.command(
        name="stop_notices",
        description="Stop automatic UIU notice updates in this server",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def stop_notices(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild_id is not None
        try:
            disabled = await notice_store.disable(interaction.guild_id)
        except NoticeStoreError:
            await interaction.followup.send(
                "Notice settings could not be read safely. Check the bot logs before retrying.",
                ephemeral=True,
            )
            return
        message = (
            "Automatic notice posting has been disabled for this server."
            if disabled
            else "Automatic notice posting was not enabled for this server."
        )
        await interaction.followup.send(message, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Setup(client))
