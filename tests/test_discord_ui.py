import asyncio
from decimal import Decimal
import unittest

import discord

from commands.cgpa import (
    CalculatorSession,
    CoursePickerView,
    DashboardView,
    calculator_embed,
)
from commands.help import HelpView, help_embed
from services.grading import PlannedCourse


class DiscordUiTests(unittest.TestCase):
    def test_calculator_dashboard_is_compact_and_action_focused(self) -> None:
        async def scenario() -> None:
            session = CalculatorSession(user_id=1001)
            view = DashboardView(session)
            self.assertEqual(len(view.children), 6)
            self.assertTrue(view.calculate.disabled)
            self.assertTrue(view.remove_course.disabled)
            embed = calculator_embed(session)
            self.assertEqual(embed.title, "UIU CGPA Calculator")
            self.assertEqual(len(embed.fields), 2)

        asyncio.run(scenario())

    def test_course_picker_fits_discord_component_rows(self) -> None:
        async def scenario() -> None:
            session = CalculatorSession(
                user_id=1001,
                completed_credits=Decimal("30"),
                current_cgpa=Decimal("2.50"),
            )
            view = CoursePickerView(session)
            rows = [item.row for item in view.children]
            self.assertLessEqual(max(rows), 4)
            self.assertEqual(len(view.credit_select.options), 11)
            self.assertEqual(len(view.grade_select.options), 11)
            self.assertFalse(view.retake_toggle.disabled)

        asyncio.run(scenario())

    def test_dashboard_result_keeps_courses_readable(self) -> None:
        session = CalculatorSession(
            user_id=1001,
            courses=[PlannedCourse(Decimal("3"), "A-")],
        )
        embed = calculator_embed(session)
        self.assertIn("3 credits", embed.fields[1].value)
        self.assertIn("A-", embed.fields[1].value)

    def test_help_uses_navigation_instead_of_full_command_dump(self) -> None:
        async def scenario() -> None:
            view = HelpView(user_id=1001, avatar_url=None)
            self.assertEqual(len(view.children), 3)
            self.assertTrue(any(isinstance(item, discord.ui.Select) for item in view.children))
            embed = help_embed("home", None)
            self.assertIn("/cgpa calculator", embed.description)
            self.assertLess(len(embed.description), 900)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
