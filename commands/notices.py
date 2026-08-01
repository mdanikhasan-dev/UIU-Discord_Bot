"""On-demand and scheduled delivery of public UIU notices."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config.settings import BOT_ACCENT_COLOR, NOTICE_CHECK_INTERVAL_MINUTES
from services.notice_store import NoticeStoreError, notice_store
from utils.fetch_notices import fetch_notices


logger = logging.getLogger(__name__)


class Notices(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.check_notices_loop.start()

    def cog_unload(self) -> None:
        self.check_notices_loop.cancel()

    @app_commands.command(name="notices", description="Show the latest three UIU notices")
    @app_commands.checks.cooldown(2, 20.0, key=lambda i: i.user.id)
    async def notices(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        notices = await fetch_notices()
        if not notices:
            await interaction.followup.send(
                "The UIU notice page could not be read right now. Please try again later.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Latest UIU notices",
            description="Links open the original notice on UIU's website.",
            color=BOT_ACCENT_COLOR,
        )
        if self.client.user:
            embed.set_thumbnail(url=str(self.client.user.display_avatar.url))
        for title, link in notices[:3]:
            embed.add_field(name=title[:256], value=f"[Read on uiu.ac.bd]({link})", inline=False)
        await interaction.followup.send(embed=embed)

    @tasks.loop(minutes=NOTICE_CHECK_INTERVAL_MINUTES)
    async def check_notices_loop(self) -> None:
        try:
            await self._run_notice_check()
        except Exception:
            logger.exception("Scheduled notice check failed")

    async def _run_notice_check(self) -> None:
        latest = await fetch_notices()
        if not latest:
            return
        try:
            servers = await notice_store.snapshot()
        except NoticeStoreError:
            logger.exception("Notice state could not be read; scheduled delivery skipped")
            return

        delivered_count = 0
        for server_id, server in servers.items():
            channel_id = server.get("notice_channel_id")
            if not channel_id:
                continue
            channel = self.client.get_channel(channel_id)
            if channel is None or not hasattr(channel, "send"):
                continue

            seen = set(server.get("seen_notices", []))
            delivered_links: list[str] = []
            for title, link in reversed(latest):
                if link in seen:
                    continue
                embed = discord.Embed(
                    title=f"New UIU notice: {title}"[:256],
                    description="A new item appeared on the public UIU notice board.",
                    url=link,
                    color=BOT_ACCENT_COLOR,
                )
                if self.client.user:
                    embed.set_thumbnail(url=str(self.client.user.display_avatar.url))
                embed.add_field(
                    name="Original notice",
                    value=f"[Read on uiu.ac.bd]({link})",
                    inline=False,
                )
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    logger.warning("Notice delivery skipped because a configured channel denied access")
                    break
                except discord.HTTPException:
                    logger.exception("Discord rejected a scheduled notice message")
                    break
                delivered_links.append(link)
                seen.add(link)
                delivered_count += 1
            try:
                await notice_store.mark_seen(server_id, delivered_links)
            except NoticeStoreError:
                logger.exception("Delivered notice links could not be recorded atomically")

        if delivered_count:
            logger.info("Delivered %d new UIU notice message(s)", delivered_count)

    @check_notices_loop.before_loop
    async def before_check_notices_loop(self) -> None:
        await self.client.wait_until_ready()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Notices(client))
