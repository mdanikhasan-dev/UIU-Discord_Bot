"""
commands/setup.py
─────────────────
Admin slash commands:
  /setup          — configures the notice channel for this server
  /stop_notices   — disables automatic notice posting for this server

Fix: file I/O now runs inside asyncio.to_thread() to avoid blocking
the event loop on slow/shared hosting.
"""

import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands

MEMORY_FILE = "data/notices_memory.json"


def _load_memory_sync() -> dict:
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "servers" not in data:
                data["servers"] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"servers": {}}


def _save_memory_sync(memory_data: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=4, ensure_ascii=False)


class Setup(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    async def _load_memory(self) -> dict:
        return await asyncio.to_thread(_load_memory_sync)

    async def _save_memory(self, memory_data: dict) -> None:
        await asyncio.to_thread(_save_memory_sync, memory_data)

    # ── /setup ────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="setup",
        description="Set the channel for automatic notice updates",
    )
    @app_commands.describe(channel="The channel to post new notices in")
    @app_commands.default_permissions(administrator=True)
    async def setup_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        server_id = str(interaction.guild.id)
        memory = await self._load_memory()

        if server_id not in memory["servers"]:
            memory["servers"][server_id] = {
                "notice_channel_id": None,
                "seen_notices": [],
            }

        memory["servers"][server_id]["notice_channel_id"] = channel.id
        await self._save_memory(memory)

        await interaction.followup.send(
            f"✅ Done! New UIU notices will be posted in {channel.mention}."
        )

    # ── /stop_notices ─────────────────────────────────────────────────────────

    @app_commands.command(
        name="stop_notices",
        description="Stop automatic notice updates in this server",
    )
    @app_commands.default_permissions(administrator=True)
    async def stop_notices(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        server_id = str(interaction.guild.id)
        memory = await self._load_memory()

        if (
            server_id in memory["servers"]
            and memory["servers"][server_id].get("notice_channel_id")
        ):
            memory["servers"][server_id]["notice_channel_id"] = None
            await self._save_memory(memory)
            await interaction.followup.send(
                "✅ Automatic notice posting has been disabled for this server."
            )
        else:
            await interaction.followup.send(
                "ℹ️ Automatic notices are not enabled in this server anyway."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Setup(client))
