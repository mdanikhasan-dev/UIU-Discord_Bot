"""A guided, private UIU CGPA calculator built with native Discord controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import BOT_ACCENT_COLOR
from services.grading import (
    GRADE_BANDS,
    GRADE_POINTS,
    UIU_GRADING_SOURCE,
    CgpaProjection,
    PlannedCourse,
    calculate_cgpa_plan,
    format_decimal,
)


MAX_SESSION_COURSES = 10
CREDIT_OPTIONS = (
    Decimal("0.5"), Decimal("1"), Decimal("1.5"), Decimal("2"),
    Decimal("2.5"), Decimal("3"), Decimal("3.5"), Decimal("4"),
    Decimal("4.5"), Decimal("5"), Decimal("6"),
)


@dataclass
class CalculatorSession:
    user_id: int
    avatar_url: str | None = None
    completed_credits: Decimal | None = None
    current_cgpa: Decimal | None = None
    courses: list[PlannedCourse] = field(default_factory=list)


def _course_lines(courses: list[PlannedCourse]) -> str:
    if not courses:
        return "No courses added yet. Select **Add course** to begin."
    lines: list[str] = []
    for index, course in enumerate(courses, start=1):
        credits = format_decimal(course.credits).rstrip("0").rstrip(".")
        if course.previous_grade:
            detail = f"{course.previous_grade} → {course.grade} · retake"
        else:
            detail = f"{course.grade} · {GRADE_POINTS[course.grade]:.2f}"
        lines.append(f"`{index:02}`  **{credits} credits**  ·  {detail}")
    return "\n".join(lines)


def calculator_embed(
    session: CalculatorSession, result: CgpaProjection | None = None
) -> discord.Embed:
    embed = discord.Embed(
        title="UIU CGPA Calculator",
        description="Build this trimester one course at a time.",
        color=BOT_ACCENT_COLOR,
    )
    if session.avatar_url:
        embed.set_thumbnail(url=session.avatar_url)
    if session.completed_credits is None:
        standing = "Not set · optional unless you are adding a retake"
    else:
        standing = (
            f"**{format_decimal(session.current_cgpa)} CGPA** · "
            f"{format_decimal(session.completed_credits)} completed credits"
        )
    embed.add_field(name="Current standing", value=standing, inline=False)
    embed.add_field(
        name=f"This trimester · {len(session.courses)}/{MAX_SESSION_COURSES} courses",
        value=_course_lines(session.courses),
        inline=False,
    )
    if result is not None:
        embed.add_field(
            name="Result",
            value=(
                f"**Trimester GPA:** {format_decimal(result.term_gpa)}\n"
                + (
                    f"**Projected CGPA:** {format_decimal(result.projected_cgpa)}\n"
                    if result.projected_cgpa is not None
                    else "**Projected CGPA:** add current standing to see it\n"
                )
                + f"**Trimester credits:** {format_decimal(result.term_credits)}"
            ),
            inline=False,
        )
    embed.set_footer(
        text="Private session · nothing is saved · UIU's official scale is used"
    )
    return embed


def picker_embed(session: CalculatorSession, course_number: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"Course {course_number}",
        description=(
            "Choose the credit value and expected grade below. "
            "Use Retake only when the course already exists in your current CGPA."
        ),
        color=BOT_ACCENT_COLOR,
    )
    embed.add_field(
        name="Selected",
        value="Credits: **not selected**\nGrade: **not selected**",
        inline=False,
    )
    return embed


class OwnedView(discord.ui.View):
    def __init__(self, session: CalculatorSession) -> None:
        super().__init__(timeout=900)
        self.session = session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.session.user_id:
            return True
        await interaction.response.send_message(
            "Start your own private calculator with `/cgpa calculator`.", ephemeral=True
        )
        return False


class CreditSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Credits",
            min_values=1,
            max_values=1,
            row=0,
            options=[
                discord.SelectOption(
                    label=f"{format_decimal(value).rstrip('0').rstrip('.')} credits",
                    value=str(value),
                )
                for value in CREDIT_OPTIONS
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, CoursePickerView)
        self.view.credits = Decimal(self.values[0])
        self.placeholder = f"Credits · {self.values[0]}"
        await interaction.response.edit_message(
            embed=self.view.current_embed(), view=self.view
        )


class GradeSelect(discord.ui.Select):
    def __init__(self, *, previous: bool = False) -> None:
        placeholder = "Previous grade · retakes only" if previous else "Grade"
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            row=2 if previous else 1,
            disabled=previous,
            options=[
                discord.SelectOption(
                    label=f"{band.grade} · {band.point:.2f}", value=band.grade
                )
                for band in GRADE_BANDS
            ],
        )
        self.previous = previous

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, CoursePickerView)
        if self.previous:
            self.view.previous_grade = self.values[0]
            self.placeholder = f"Previous grade · {self.values[0]}"
        else:
            self.view.grade = self.values[0]
            self.placeholder = f"Grade · {self.values[0]}"
        await interaction.response.edit_message(
            embed=self.view.current_embed(), view=self.view
        )


class CoursePickerView(OwnedView):
    def __init__(self, session: CalculatorSession) -> None:
        super().__init__(session)
        self.credits: Decimal | None = None
        self.grade: str | None = None
        self.previous_grade: str | None = None
        self.is_retake = False
        self.credit_select = CreditSelect()
        self.grade_select = GradeSelect()
        self.previous_select = GradeSelect(previous=True)
        self.add_item(self.credit_select)
        self.add_item(self.grade_select)
        self.add_item(self.previous_select)
        if session.completed_credits is None:
            self.retake_toggle.disabled = True

    def current_embed(self) -> discord.Embed:
        embed = picker_embed(self.session, len(self.session.courses) + 1)
        credits = (
            format_decimal(self.credits).rstrip("0").rstrip(".")
            if self.credits is not None
            else "not selected"
        )
        grade = self.grade or "not selected"
        retake = (
            f"\nRetake: **{self.previous_grade or 'select previous grade'} → {grade}**"
            if self.is_retake
            else ""
        )
        embed.set_field_at(
            0,
            name="Selected",
            value=f"Credits: **{credits}**\nGrade: **{grade}**{retake}",
            inline=False,
        )
        return embed

    @discord.ui.button(
        label="Retake",
        style=discord.ButtonStyle.secondary,
        row=3,
        custom_id="cgpa_retake",
    )
    async def retake_toggle(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.is_retake = not self.is_retake
        self.previous_select.disabled = not self.is_retake
        if not self.is_retake:
            self.previous_grade = None
            self.previous_select.placeholder = "Previous grade · retakes only"
        button.label = "Retake · on" if self.is_retake else "Retake"
        button.style = (
            discord.ButtonStyle.primary if self.is_retake else discord.ButtonStyle.secondary
        )
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="Save course", style=discord.ButtonStyle.success, row=3)
    async def save_course(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.credits is None or self.grade is None:
            await interaction.response.send_message(
                "Choose both credits and a grade first.", ephemeral=True
            )
            return
        if self.is_retake and self.previous_grade is None:
            await interaction.response.send_message(
                "Choose the previous grade for this retake.", ephemeral=True
            )
            return
        self.session.courses.append(
            PlannedCourse(
                credits=self.credits,
                grade=self.grade,
                previous_grade=self.previous_grade if self.is_retake else None,
            )
        )
        self.stop()
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=3)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.stop()
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )


class CurrentStandingModal(discord.ui.Modal, title="Current standing"):
    completed = discord.ui.TextInput(
        label="Completed credits",
        placeholder="Example: 60",
        min_length=1,
        max_length=6,
    )
    cgpa = discord.ui.TextInput(
        label="Current CGPA",
        placeholder="Example: 2.85",
        min_length=1,
        max_length=4,
    )

    def __init__(self, session: CalculatorSession) -> None:
        super().__init__()
        self.session = session
        if session.completed_credits is not None:
            self.completed.default = str(session.completed_credits)
            self.cgpa.default = str(session.current_cgpa)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            credits = Decimal(self.completed.value).quantize(Decimal("0.01"))
            cgpa = Decimal(self.cgpa.value).quantize(Decimal("0.01"))
        except InvalidOperation:
            await interaction.response.send_message(
                "Use numbers only, such as 60 and 2.85.", ephemeral=True
            )
            return
        if not credits.is_finite() or not cgpa.is_finite():
            await interaction.response.send_message(
                "Use ordinary numbers only, such as 60 and 2.85.", ephemeral=True
            )
            return
        if credits < 0 or credits > 300:
            await interaction.response.send_message(
                "Completed credits must be from 0 to 300.", ephemeral=True
            )
            return
        if cgpa < 0 or cgpa > 4:
            await interaction.response.send_message(
                "Current CGPA must be from 0.00 to 4.00.", ephemeral=True
            )
            return
        if credits == 0 and cgpa != 0:
            await interaction.response.send_message(
                "CGPA must be 0.00 when completed credits are 0.", ephemeral=True
            )
            return
        self.session.completed_credits = credits
        self.session.current_cgpa = cgpa
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )


class RemoveCourseSelect(discord.ui.Select):
    def __init__(self, session: CalculatorSession) -> None:
        super().__init__(
            placeholder="Choose a course to remove",
            row=0,
            options=[
                discord.SelectOption(
                    label=f"Course {index}",
                    description=(
                        f"{format_decimal(course.credits).rstrip('0').rstrip('.')} credits · "
                        f"{course.previous_grade + ' → ' if course.previous_grade else ''}{course.grade}"
                    )[:100],
                    value=str(index - 1),
                )
                for index, course in enumerate(session.courses, start=1)
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert isinstance(self.view, RemoveCourseView)
        self.view.session.courses.pop(int(self.values[0]))
        self.view.stop()
        await interaction.response.edit_message(
            embed=calculator_embed(self.view.session),
            view=DashboardView(self.view.session),
        )


class RemoveCourseView(OwnedView):
    def __init__(self, session: CalculatorSession) -> None:
        super().__init__(session)
        self.add_item(RemoveCourseSelect(session))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, row=1)
    async def back(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.stop()
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )


class DashboardView(OwnedView):
    def __init__(self, session: CalculatorSession) -> None:
        super().__init__(session)
        self.remove_course.disabled = not session.courses
        self.calculate.disabled = not session.courses

    @discord.ui.button(label="Add course", style=discord.ButtonStyle.primary, row=0)
    async def add_course(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if len(self.session.courses) >= MAX_SESSION_COURSES:
            await interaction.response.send_message(
                f"This calculator supports up to {MAX_SESSION_COURSES} courses.",
                ephemeral=True,
            )
            return
        self.stop()
        picker = CoursePickerView(self.session)
        await interaction.response.edit_message(
            embed=picker.current_embed(), view=picker
        )

    @discord.ui.button(label="Current standing", style=discord.ButtonStyle.secondary, row=0)
    async def current_standing(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(CurrentStandingModal(self.session))

    @discord.ui.button(label="Calculate", style=discord.ButtonStyle.success, row=0)
    async def calculate(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        try:
            result = calculate_cgpa_plan(
                self.session.courses,
                current_cgpa=self.session.current_cgpa,
                completed_credits=self.session.completed_credits,
            )
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=calculator_embed(self.session, result), view=DashboardView(self.session)
        )

    @discord.ui.button(label="Remove course", style=discord.ButtonStyle.secondary, row=1)
    async def remove_course(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Remove a course",
                description=_course_lines(self.session.courses),
                color=BOT_ACCENT_COLOR,
            ),
            view=RemoveCourseView(self.session),
        )

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.secondary, row=1)
    async def reset(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.session.completed_credits = None
        self.session.current_cgpa = None
        self.session.courses.clear()
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )

    @discord.ui.button(label="Grade scale", style=discord.ButtonStyle.secondary, row=1)
    async def grade_scale(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        lines = [
            f"**{band.grade}** · {band.point:.2f} · {band.minimum_mark}–{band.maximum_mark}%"
            for band in GRADE_BANDS
        ]
        embed = discord.Embed(
            title="UIU grading scale",
            description="\n".join(lines),
            color=BOT_ACCENT_COLOR,
            url=UIU_GRADING_SOURCE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Cgpa(
    commands.GroupCog,
    group_name="cgpa",
    group_description="A guided UIU CGPA calculator",
):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(
        name="calculator",
        description="Open a private credit-and-grade CGPA calculator",
    )
    @app_commands.checks.cooldown(2, 10.0, key=lambda interaction: interaction.user.id)
    async def calculator(self, interaction: discord.Interaction) -> None:
        avatar_url = (
            str(self.client.user.display_avatar.url) if self.client.user else None
        )
        session = CalculatorSession(
            user_id=interaction.user.id,
            avatar_url=avatar_url,
        )
        await interaction.response.send_message(
            embed=calculator_embed(session),
            view=DashboardView(session),
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Cgpa(client))
