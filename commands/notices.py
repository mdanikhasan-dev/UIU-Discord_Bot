"""
commands/notices.py
───────────────────
Slash commands:
  /notices  — shows the latest 3 UIU notices on demand
  (auto-posting loop) — posts new notices to configured channels automatically

Key fixes in this version:
  1. Loop interval raised from 1 min to NOTICE_CHECK_INTERVAL_MINUTES (5 min).
     One HTTP scrape per minute was excessive and risked IP blocks.
  2. Entire loop body wrapped in try/except so a single bad iteration
     cannot kill the task permanently (which was the primary cause of
     the "alive but not responding" symptom).
  3. _save_memory() now only called when data actually changed (was
     called on every tick regardless).
  4. seen_notices list is capped at MAX_SEEN_NOTICES entries to prevent
     unbounded growth of the JSON file over many months.
  5. File I/O (_load_memory / _save_memory) offloaded to a thread via
     asyncio.to_thread so it cannot block the event loop on slow hosts.
  6. on_error hook logs loop failures instead of silently swallowing them.
"""

import asyncio
import json
import traceback
from typing import List, Tuple

import discord
from discord import app_commands
from discord.ext import commands, tasks

from config.settings import MAX_SEEN_NOTICES, NOTICE_CHECK_INTERVAL_MINUTES
from utils.fetch_notices import fetch_notices

MEMORY_FILE = "data/notices_memory.json"


# ─── Sync helpers (run inside asyncio.to_thread) ──────────────────────────────

def _load_memory_sync() -> dict:
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure required structure exists
            if "servers" not in data:
                data["servers"] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"servers": {}}


def _save_memory_sync(memory_data: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=4, ensure_ascii=False)


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Notices(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.check_notices_loop.start()

    def cog_unload(self) -> None:
        """Stop the loop cleanly when the cog is unloaded."""
        self.check_notices_loop.cancel()

    # ── Async wrappers for file I/O ────────────────────────────────────────────

    async def _load_memory(self) -> dict:
        return await asyncio.to_thread(_load_memory_sync)

    async def _save_memory(self, memory_data: dict) -> None:
        await asyncio.to_thread(_save_memory_sync, memory_data)

    # ── /notices slash command ─────────────────────────────────────────────────

    @app_commands.command(name="notices", description="Get the latest 3 UIU notices")
    async def notices(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        notices_list: List[Tuple[str, str]] = await fetch_notices()

        if not notices_list:
            await interaction.followup.send(
                "Sorry, I couldn't fetch any notices right now. The UIU website may be down."
            )
            return

        embed = discord.Embed(
            title="UIU Latest Notices",
            description="Here are the top 3 notices from the board.",
            color=0xCCCCCC,
        )
        embed.set_thumbnail(
            url="https://i.ibb.co.com/ZphvQT2g/meme-20251103070415-139132.gif"
        )

        for title, link in notices_list[:3]:
            embed.add_field(name=title, value=f"[Click to Read]({link})", inline=False)

        await interaction.followup.send(embed=embed)

    # ── Background notice-checking loop ───────────────────────────────────────

    @tasks.loop(minutes=NOTICE_CHECK_INTERVAL_MINUTES)
    async def check_notices_loop(self) -> None:
        # Wrap everything so a single bad tick never kills the loop.
        try:
            await self._run_notice_check()
        except Exception:
            print("[check_notices_loop] Unhandled exception in loop tick:")
            traceback.print_exc()

    async def _run_notice_check(self) -> None:
        latest_notices = await fetch_notices()
        if not latest_notices:
            return  # fetch failed — skip this tick, try again next time

        memory = await self._load_memory()
        memory_changed = False

        for server_id, server_data in memory["servers"].items():
            channel_id = server_data.get("notice_channel_id")
            if not channel_id:
                continue

            channel = self.client.get_channel(channel_id)
            if not channel:
                continue

            seen_notices: List[str] = server_data.get("seen_notices", [])

            # Walk notices oldest-first so they post in chronological order.
            for title, link in reversed(latest_notices):
                if link in seen_notices:
                    continue

                embed = discord.Embed(
                    title=f"New UIU Notice: {title}",
                    description="A new notice has been posted on the UIU website.",
                    color=0xCCCCCC,
                    url=link,
                )
                embed.set_thumbnail(
                    url="https://i.ibb.co.com/ZphvQT2g/meme-20251103070415-139132.gif"
                )
                embed.add_field(
                    name="Click to Read",
                    value=f"[Read the full notice here]({link})",
                    inline=False,
                )

                try:
                    await channel.send(embed=embed)
                    seen_notices.append(link)
                    memory_changed = True
                except discord.Forbidden:
                    print(f"[notices] Missing permissions for channel {channel_id}")
                except discord.HTTPException as e:
                    print(f"[notices] Discord error posting to {channel_id}: {e}")

            # Cap list size — removes the oldest entries first.
            if len(seen_notices) > MAX_SEEN_NOTICES:
                seen_notices = seen_notices[-MAX_SEEN_NOTICES:]
                memory_changed = True

            memory["servers"][server_id]["seen_notices"] = seen_notices

        # Only write to disk if something actually changed.
        if memory_changed:
            await self._save_memory(memory)

    @check_notices_loop.before_loop
    async def before_check_notices_loop(self) -> None:
        await self.client.wait_until_ready()

    @check_notices_loop.error
    async def on_check_notices_error(self, error: Exception) -> None:
        # This fires if the loop itself errors before our inner try/except
        # catches it.  Log and allow the loop to restart.
        print(f"[check_notices_loop] Loop-level error: {type(error).__name__}: {error}")
        traceback.print_exc()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Notices(client))
