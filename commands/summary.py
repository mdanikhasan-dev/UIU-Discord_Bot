"""Private `/summary` command with local-first processing."""

from __future__ import annotations

from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import GROQ_API_KEY, GROQ_MODEL
from services.summarization import SummarizationError, summarize


MAX_ATTACHMENT_BYTES = 128 * 1024
ALLOWED_ATTACHMENTS = {".txt", ".md", ".csv"}


async def _read_input(
    text: str | None, attachment: discord.Attachment | None
) -> str:
    if bool(text) == bool(attachment):
        raise SummarizationError("Provide either pasted text or one attachment, not both.")
    if text:
        return text
    assert attachment is not None
    if Path(attachment.filename).suffix.lower() not in ALLOWED_ATTACHMENTS:
        raise SummarizationError("Attachment must be a .txt, .md, or .csv file.")
    if attachment.size > MAX_ATTACHMENT_BYTES:
        raise SummarizationError("Attachment is too large. The limit is 128 KB.")
    try:
        return (await attachment.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SummarizationError("Attachment must use UTF-8 text encoding.") from exc


class Summary(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="summary",
        description="Summarize pasted text or a text file without saving it",
    )
    @app_commands.describe(
        text="Text to summarize (use an attachment for longer content)",
        attachment="A UTF-8 .txt, .md, or .csv file (maximum 128 KB)",
        style="Length and format of the summary",
        engine="Private stays local; AI explicitly sends text to Groq",
    )
    @app_commands.choices(
        style=[
            app_commands.Choice(name="Concise", value="concise"),
            app_commands.Choice(name="Detailed", value="detailed"),
            app_commands.Choice(name="Bullet points", value="bullets"),
        ],
        engine=[
            app_commands.Choice(name="Private · processed locally", value="private"),
            app_commands.Choice(name="AI · sends text to Groq", value="ai"),
        ],
    )
    @app_commands.checks.cooldown(2, 20.0, key=lambda i: i.user.id)
    async def summary(
        self,
        interaction: discord.Interaction,
        text: str | None = None,
        attachment: discord.Attachment | None = None,
        style: app_commands.Choice[str] | None = None,
        engine: app_commands.Choice[str] | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        style_value = style.value if style else "concise"
        engine_value = engine.value if engine else "private"
        try:
            supplied = await _read_input(text, attachment)
            result = await summarize(
                supplied,
                style_value,
                engine_value,
                groq_api_key=GROQ_API_KEY,
                groq_model=GROQ_MODEL,
            )
        except SummarizationError as exc:
            await interaction.followup.send(f"Could not summarize: {exc}", ephemeral=True)
            return

        notes = [f"Engine: {result.engine}", "Input and summary were not saved by the bot."]
        if result.input_truncated:
            notes.append("Only the first 50,000 characters were processed.")
        if result.fallback_reason:
            notes.append(f"AI was unavailable; local fallback used: {result.fallback_reason}")
        safe_summary = discord.utils.escape_mentions(result.text)
        await interaction.followup.send(
            f"**Summary**\n{safe_summary}\n\n*{' '.join(notes)}*",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Summary(client))
