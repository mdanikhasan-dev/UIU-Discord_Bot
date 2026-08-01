"""A simple private summarizer with optional, explicit cloud AI use."""

from __future__ import annotations

from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR, GROQ_API_KEY, GROQ_MODEL
from services.summarization import SummarizationError, summarize


MAX_ATTACHMENT_BYTES = 128 * 1024
ALLOWED_ATTACHMENTS = {".txt", ".md", ".csv"}


async def _read_input(
    text: str | None, attachment: discord.Attachment | None
) -> str:
    if bool(text) == bool(attachment):
        raise SummarizationError("Paste text or attach one file—not both.")
    if text:
        return text
    assert attachment is not None
    if Path(attachment.filename).suffix.lower() not in ALLOWED_ATTACHMENTS:
        raise SummarizationError("Use a .txt, .md, or .csv file.")
    if attachment.size > MAX_ATTACHMENT_BYTES:
        raise SummarizationError("The attachment limit is 128 KB.")
    try:
        return (await attachment.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SummarizationError("The attachment must use UTF-8 text encoding.") from exc


class Summary(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="summary",
        description="Turn pasted text or a text file into a clear private brief",
    )
    @app_commands.describe(
        text="Text to summarize",
        attachment="Optional UTF-8 .txt, .md, or .csv file",
        use_ai="Send this text to Groq for an AI-written summary",
    )
    @app_commands.checks.cooldown(2, 20.0, key=lambda interaction: interaction.user.id)
    async def summary(
        self,
        interaction: discord.Interaction,
        text: str | None = None,
        attachment: discord.Attachment | None = None,
        use_ai: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            supplied = await _read_input(text, attachment)
            result = await summarize(
                supplied,
                "concise",
                "ai" if use_ai else "private",
                groq_api_key=GROQ_API_KEY,
                groq_model=GROQ_MODEL,
            )
        except SummarizationError as exc:
            await interaction.followup.send(f"Could not summarize: {exc}", ephemeral=True)
            return

        embed = discord.Embed(
            title=result.label,
            description=discord.utils.escape_mentions(result.text),
            color=BOT_ACCENT_COLOR,
        )
        if result.input_truncated:
            embed.add_field(
                name="Input limit",
                value="Only the first 50,000 characters were processed.",
                inline=False,
            )
        if result.fallback_reason:
            embed.add_field(
                name="Local fallback used",
                value=result.fallback_reason,
                inline=False,
            )
        privacy = "not saved"
        if use_ai:
            privacy = "sent to Groq for this request · not saved by UIU Bot"
        embed.set_footer(text=f"{result.engine} · {privacy}")
        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Summary(client))
