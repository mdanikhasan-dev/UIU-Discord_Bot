from discord.ext import commands
from discord import app_commands
import discord

from config.settings import BOT_NAME


class Help(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="help",
        description="Shows a list of all available commands.",
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title=f"{BOT_NAME} Help Menu",
            description=(
                "Here are all the commands you can use. "
                "You can also type `/` to see them directly in Discord!"
            ),
            color=0xCCCCCC,
        )

        embed.add_field(name="Public Commands", value="─────────────────", inline=False)
        embed.add_field(name="`/poll`", value="Create a poll with up to 10 options.", inline=False)
        embed.add_field(name="`/notices`", value="Get the latest 3 notices from the UIU website.", inline=False)
        embed.add_field(name="`/calendar`", value="Shows the current academic calendar.", inline=False)
        embed.add_field(name="`/ping`", value="Checks the bot's latency.", inline=False)
        embed.add_field(name="`/about`", value="Shows information about this bot.", inline=False)

        embed.add_field(name="Admin Commands", value="─────────────────", inline=False)
        embed.add_field(name="`/setup`", value="(Admin) Sets the channel for automatic notice posts.", inline=False)
        embed.add_field(name="`/stop_notices`", value="(Admin) Stops automatic notice posts.", inline=False)

        await interaction.followup.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Help(client))
