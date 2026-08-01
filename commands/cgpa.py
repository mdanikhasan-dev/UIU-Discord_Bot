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
        return "No courses yet. Use **Add course** or **Add retake** below."
    lines: list[str] = []
    for index, course in enumerate(courses, start=1):
        credits = _credit_label(course.credits)
        if course.previous_grade:
            detail = (
                f"`{credits}`   **{course.previous_grade} → {course.grade}**\n"
                "Retake · replaces the earlier grade"
            )
        else:
            detail = (
                f"`{credits}`   **{course.grade} · "
                f"{GRADE_POINTS[course.grade]:.2f}**"
            )
        lines.append(f"**Course {index:02}**\n{detail}")
    return "\n\n".join(lines)


def _compact_number(value: Decimal) -> str:
    return format_decimal(value).rstrip("0").rstrip(".")


def _credit_label(value: Decimal) -> str:
    unit = "credit" if value == Decimal("1") else "credits"
    return f"{_compact_number(value)} {unit}"


def calculator_embed(
    session: CalculatorSession, result: CgpaProjection | None = None
) -> discord.Embed:
    embed = discord.Embed(
        title="UIU CGPA Calculator",
        description=(
            "Add regular courses or retakes, then calculate. Current standing is "
            "needed only for retakes and a projected cumulative CGPA."
        ),
        color=BOT_ACCENT_COLOR,
    )
    if session.avatar_url:
        embed.set_thumbnail(url=session.avatar_url)
    current_cgpa = (
        f"**{format_decimal(session.current_cgpa)}**"
        if session.current_cgpa is not None
        else "Not set"
    )
    completed_credits = (
        f"**{_compact_number(session.completed_credits)}**"
        if session.completed_credits is not None
        else "Not set"
    )
    embed.add_field(name="Current CGPA", value=current_cgpa, inline=True)
    embed.add_field(name="Completed credits", value=completed_credits, inline=True)
    embed.add_field(
        name="Planned courses", value=f"**{len(session.courses)}**", inline=True
    )
    embed.add_field(
        name="This trimester",
        value=_course_lines(session.courses),
        inline=False,
    )
    if result is not None:
        embed.add_field(
            name="Trimester GPA",
            value=f"**{format_decimal(result.term_gpa)}**",
            inline=True,
        )
        embed.add_field(
            name="Projected CGPA",
            value=(
                f"**{format_decimal(result.projected_cgpa)}**"
                if result.projected_cgpa is not None
                else "Set standing"
            ),
            inline=True,
        )
        embed.add_field(
            name="Trimester credits",
            value=f"**{_compact_number(result.term_credits)}**",
            inline=True,
        )
    embed.set_footer(
        text="Private session · nothing is saved · UIU's official scale is used"
    )
    return embed


def picker_embed(
    session: CalculatorSession, course_number: int, *, is_retake: bool
) -> discord.Embed:
    if is_retake:
        title = f"Add retake · Course {course_number}"
        instructions = (
            "Choose the course credits, the new expected grade, and the previous grade "
            "that is already included in your CGPA."
        )
    else:
        title = f"Add course · Course {course_number}"
        instructions = "Choose the course credits and expected grade, then save it."
    embed = discord.Embed(
        title=title,
        description=instructions,
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
                    label=_credit_label(value),
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
    def __init__(self, session: CalculatorSession, *, is_retake: bool = False) -> None:
        super().__init__(session)
        self.credits: Decimal | None = None
        self.grade: str | None = None
        self.previous_grade: str | None = None
        self.is_retake = is_retake
        self.credit_select = CreditSelect()
        self.grade_select = GradeSelect()
        self.add_item(self.credit_select)
        self.add_item(self.grade_select)
        self.previous_select: GradeSelect | None = None
        if is_retake:
            self.previous_select = GradeSelect(previous=True)
            self.previous_select.disabled = False
            self.add_item(self.previous_select)

    def current_embed(self) -> discord.Embed:
        embed = picker_embed(
            self.session,
            len(self.session.courses) + 1,
            is_retake=self.is_retake,
        )
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


class CurrentStandingModal(discord.ui.Modal, title="Current CGPA and credits"):
    completed = discord.ui.TextInput(
        label="1 · Completed credits",
        placeholder="Example: 41",
        min_length=1,
        max_length=6,
    )
    cgpa = discord.ui.TextInput(
        label="2 · Current CGPA",
        placeholder="Example: 2.00",
        min_length=1,
        max_length=4,
    )

    def __init__(
        self, session: CalculatorSession, *, next_action: str = "dashboard"
    ) -> None:
        super().__init__()
        self.session = session
        self.next_action = next_action
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
        if self.next_action == "retake":
            picker = CoursePickerView(self.session, is_retake=True)
            await interaction.response.edit_message(
                embed=picker.current_embed(), view=picker
            )
            return
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
        self.current_standing.label = (
            "Edit standing" if session.completed_credits is not None else "Set standing"
        )

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

    @discord.ui.button(label="Add retake", style=discord.ButtonStyle.primary, row=0)
    async def add_retake(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if len(self.session.courses) >= MAX_SESSION_COURSES:
            await interaction.response.send_message(
                f"This calculator supports up to {MAX_SESSION_COURSES} courses.",
                ephemeral=True,
            )
            return
        if self.session.completed_credits is None:
            await interaction.response.send_modal(
                CurrentStandingModal(self.session, next_action="retake")
            )
            return
        self.stop()
        picker = CoursePickerView(self.session, is_retake=True)
        await interaction.response.edit_message(
            embed=picker.current_embed(), view=picker
        )

    @discord.ui.button(label="Set standing", style=discord.ButtonStyle.secondary, row=2)
    async def current_standing(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(CurrentStandingModal(self.session))

    @discord.ui.button(label="Calculate CGPA", style=discord.ButtonStyle.success, row=1)
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

    @discord.ui.button(label="Remove course", style=discord.ButtonStyle.secondary, row=2)
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

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.secondary, row=3)
    async def reset(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.session.completed_credits = None
        self.session.current_cgpa = None
        self.session.courses.clear()
        await interaction.response.edit_message(
            embed=calculator_embed(self.session), view=DashboardView(self.session)
        )

    @discord.ui.button(label="Grade scale", style=discord.ButtonStyle.secondary, row=3)
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
