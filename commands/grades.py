"""Private UIU grade-scale, GPA, CGPA, and planning commands."""

from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from services.grading import (
    GRADE_BANDS,
    MINIMUM_CGPA,
    UIU_GRADING_SOURCE,
    UIU_RETAKE_SOURCE,
    calculate_academic_summary,
    format_decimal,
    grade_for_mark,
    parse_course_rows,
    project_cgpa,
    required_gpa,
)


MAX_ATTACHMENT_BYTES = 128 * 1024
ALLOWED_ATTACHMENTS = {".csv", ".tsv", ".txt"}


def _decimal(value: float) -> Decimal:
    return Decimal(str(value))


async def _read_grade_input(
    rows: str | None, attachment: discord.Attachment | None
) -> str:
    if bool(rows) == bool(attachment):
        raise ValueError("Provide either pasted rows or one attachment, not both.")
    if rows:
        return rows
    assert attachment is not None
    suffix = Path(attachment.filename).suffix.lower()
    if suffix not in ALLOWED_ATTACHMENTS:
        raise ValueError("Attachment must be a .csv, .tsv, or .txt file.")
    if attachment.size > MAX_ATTACHMENT_BYTES:
        raise ValueError("Attachment is too large. The limit is 128 KB.")
    try:
        payload = await attachment.read()
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Attachment must use UTF-8 text encoding.") from exc


class GradeTools(
    commands.GroupCog,
    group_name="grade",
    group_description="UIU grade scale, GPA estimates, and planning tools",
):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="scale", description="Show the official UIU grade scale")
    async def scale(self, interaction: discord.Interaction) -> None:
        lines = [
            f"**{band.grade}** · {band.point:.2f} · {band.minimum_mark}–{band.maximum_mark}%"
            for band in GRADE_BANDS
        ]
        embed = discord.Embed(
            title="UIU grading scale",
            description="\n".join(lines),
        )
        embed.add_field(
            name="Credit rule",
            value=(
                "D or higher earns course credit. F earns no credit. "
                "W and I are not included in GPA calculations."
            ),
            inline=False,
        )
        embed.add_field(
            name="Official source",
            value=f"[UIU grading and performance evaluation]({UIU_GRADING_SOURCE})",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="marks", description="Convert a percentage mark to its UIU letter grade"
    )
    @app_commands.describe(mark="Percentage mark from 0 to 100")
    async def marks(
        self, interaction: discord.Interaction, mark: app_commands.Range[int, 0, 100]
    ) -> None:
        band = grade_for_mark(mark)
        await interaction.response.send_message(
            f"**{mark}% → {band.grade} ({band.point:.2f})**\n"
            f"Official UIU range: {band.minimum_mark}–{band.maximum_mark}%.",
            ephemeral=True,
        )

    @app_commands.command(
        name="calculate",
        description="Calculate term GPAs and a portal-compatible CGPA estimate",
    )
    @app_commands.describe(
        rows="Paste rows: term,course,credits,grade",
        attachment="Or attach a UTF-8 .csv, .tsv, or .txt file",
    )
    @app_commands.checks.cooldown(2, 15.0, key=lambda i: i.user.id)
    async def calculate(
        self,
        interaction: discord.Interaction,
        rows: str | None = None,
        attachment: discord.Attachment | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            supplied = await _read_grade_input(rows, attachment)
            parsed = parse_course_rows(supplied)
            summary = calculate_academic_summary(parsed.attempts)
        except ValueError as exc:
            await interaction.followup.send(f"Could not calculate: {exc}", ephemeral=True)
            return

        portal = (
            format_decimal(summary.portal_cgpa)
            if summary.portal_cgpa is not None
            else "Not available"
        )
        transcript = (
            format_decimal(summary.transcript_cgpa)
            if summary.transcript_cgpa is not None
            else "Not available"
        )
        standing = (
            "At or above UIU's 2.00 minimum"
            if summary.meets_minimum_cgpa
            else "Below UIU's 2.00 minimum"
        )
        term_lines = [
            f"**{item.term}:** {format_decimal(item.gpa)} across "
            f"{format_decimal(item.attempted_credits)} attempted credits"
            for item in summary.term_results
            if item.gpa is not None
        ]

        embed = discord.Embed(
            title="Academic estimate",
            description=(
                f"**Portal-compatible CGPA:** {portal}\n"
                f"**Passing-course CGPA:** {transcript}\n"
                f"**Standing check:** {standing}"
            ),
        )
        embed.add_field(
            name="Credits",
            value=(
                f"Attempted: **{format_decimal(summary.attempted_credits)}**\n"
                f"Earned: **{format_decimal(summary.earned_credits)}**"
            ),
        )
        embed.add_field(
            name="Attempts",
            value=(
                f"Effective courses: **{summary.effective_courses}**\n"
                f"Earlier graded attempts replaced: **{summary.replaced_attempts}**\n"
                f"W / I rows excluded: **{summary.withdrawals + summary.incompletes}**"
            ),
        )
        if term_lines:
            embed.add_field(name="Term GPA", value="\n".join(term_lines)[:1024], inline=False)
        if parsed.warnings:
            embed.add_field(
                name="Rows skipped",
                value="\n".join(parsed.warnings[:6])[:1024],
                inline=False,
            )
        embed.add_field(
            name="How this estimate works",
            value=(
                "F counts in attempted credits but earns none. W and I are excluded. "
                "For repeated course codes, the latest graded attempt is used. "
                f"[Official grade scale]({UIU_GRADING_SOURCE}) · "
                f"[Retake policy]({UIU_RETAKE_SOURCE})"
            ),
            inline=False,
        )
        embed.set_footer(
            text=(
                "Advisory calculation only. UIU's public policy does not document every "
                "UCAM replacement detail; verify official results in UCAM. Inputs are not saved."
            )
        )
        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(
        name="project", description="Project CGPA after a planned set of credits"
    )
    @app_commands.describe(
        current_cgpa="Current CGPA from 0.00 to 4.00",
        completed_credits="Credits already included in the CGPA",
        planned_credits="Upcoming attempted credits",
        planned_gpa="GPA you expect across the planned credits",
    )
    async def project(
        self,
        interaction: discord.Interaction,
        current_cgpa: float,
        completed_credits: float,
        planned_credits: float,
        planned_gpa: float,
    ) -> None:
        try:
            projected = project_cgpa(
                _decimal(current_cgpa),
                _decimal(completed_credits),
                _decimal(planned_credits),
                _decimal(planned_gpa),
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        minimum_note = (
            "This is at or above UIU's 2.00 minimum."
            if projected >= MINIMUM_CGPA
            else "This is below UIU's 2.00 minimum."
        )
        await interaction.response.send_message(
            f"Projected CGPA: **{format_decimal(projected)}**\n{minimum_note}",
            ephemeral=True,
        )

    @app_commands.command(
        name="target", description="Find the GPA needed to reach a target CGPA"
    )
    @app_commands.describe(
        current_cgpa="Current CGPA from 0.00 to 4.00",
        completed_credits="Credits already included in the CGPA",
        planned_credits="Upcoming attempted credits",
        target_cgpa="CGPA you want after those credits",
    )
    async def target(
        self,
        interaction: discord.Interaction,
        current_cgpa: float,
        completed_credits: float,
        planned_credits: float,
        target_cgpa: float,
    ) -> None:
        try:
            needed = required_gpa(
                _decimal(current_cgpa),
                _decimal(completed_credits),
                _decimal(planned_credits),
                _decimal(target_cgpa),
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        if needed > Decimal("4.00"):
            response = (
                f"That target is not reachable in the planned credits. It would require "
                f"a **{format_decimal(needed)} GPA**, above the 4.00 maximum."
            )
        else:
            response = f"Required GPA across the planned credits: **{format_decimal(needed)}**"
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(
        name="template", description="Download a blank-safe grade input example"
    )
    async def template(self, interaction: discord.Interaction) -> None:
        example = (
            "term,course,credits,grade\n"
            "261,CSE 1001,3,A-\n"
            "261,ENG 1001,3,B+\n"
            "262,CSE 1001,3,A\n"
        )
        file = discord.File(io.BytesIO(example.encode("utf-8")), filename="uiu-grades-example.csv")
        await interaction.response.send_message(
            "Use one completed course per row. Keep rows in chronological order. "
            "The file is processed in memory and is not saved by the bot.",
            file=file,
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GradeTools(client))
