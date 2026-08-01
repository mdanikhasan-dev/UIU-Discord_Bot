"""Private command directory generated from the bot's supported feature set."""

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_NAME


class Help(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="help", description="Show UIU Bot's command directory")
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title=f"{BOT_NAME} commands",
            description="Type `/` in Discord to see parameters and autocomplete.",
        )
        embed.add_field(
            name="Academic",
            value=(
                "`/grade scale` · official UIU scale\n"
                "`/grade marks` · marks to grade\n"
                "`/grade calculate` · term GPA and CGPA estimate\n"
                "`/grade project` · project a CGPA\n"
                "`/grade target` · GPA needed for a target\n"
                "`/grade template` · safe input example\n"
                "`/calendar` · verified current dates"
            ),
            inline=False,
        )
        embed.add_field(
            name="Information and utilities",
            value=(
                "`/summary` · private local or explicitly selected AI summary\n"
                "`/notices` · latest public UIU notices\n"
                "`/poll` · reaction poll\n"
                "`/ping` · Discord latency\n"
                "`/about` · version, privacy, and invite link"
            ),
            inline=False,
        )
        embed.add_field(
            name="Server administrators",
            value=(
                "`/setup` · choose the automatic notice channel\n"
                "`/stop_notices` · disable automatic notice posts"
            ),
            inline=False,
        )
        embed.set_footer(text="Grade and summary inputs are processed in memory and not saved.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Help(client))
