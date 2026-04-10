from discord.ext import commands
from discord import app_commands
import discord

from config.settings import BOT_NAME, BOT_VERSION, BOT_OWNER

CLIENT_ID = "1434163768488890549"


class About(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="about",
        description="Shows all the important details about this bot.",
    )
    async def about_command(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        invite_link = (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
        )

        embed = discord.Embed(
            title=f"About {BOT_NAME}",
            description=(
                f"{BOT_NAME} v{BOT_VERSION}. "
                "A bot for UIU notices, updates, and community info."
            ),
            color=0xCCCCCC,
        )

        try:
            embed.set_thumbnail(url=str(self.client.user.avatar.url))
        except Exception:
            pass

        embed.add_field(name="Owner / Developer", value=BOT_OWNER, inline=True)
        embed.add_field(name="Contact Email", value="anikhasan2@icloud.com", inline=True)
        embed.add_field(
            name="Status",
            value="Under active development. New features coming soon!",
            inline=False,
        )
        embed.add_field(
            name="Invite Me!",
            value=f"[Click here to add {BOT_NAME} to your server!]({invite_link})",
            inline=False,
        )

        await interaction.followup.send(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(About(client))
