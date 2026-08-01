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
            self.assertEqual(len(view.children), 7)
            self.assertTrue(view.calculate.disabled)
            self.assertTrue(view.remove_course.disabled)
            self.assertFalse(view.add_retake.disabled)
            self.assertEqual(view.current_standing.label, "Set standing")
            labels = [item.label for item in view.children if isinstance(item, discord.ui.Button)]
            self.assertIn("Add retake", labels)
            embed = calculator_embed(session)
            self.assertEqual(embed.title, "UIU CGPA Calculator")
            self.assertEqual(len(embed.fields), 4)

        asyncio.run(scenario())

    def test_course_picker_fits_discord_component_rows(self) -> None:
        async def scenario() -> None:
            session = CalculatorSession(
                user_id=1001,
                completed_credits=Decimal("30"),
                current_cgpa=Decimal("2.50"),
            )
            view = CoursePickerView(session, is_retake=True)
            rows = [item.row for item in view.children]
            self.assertLessEqual(max(rows), 4)
            self.assertEqual(len(view.credit_select.options), 11)
            self.assertEqual(len(view.grade_select.options), 11)
            self.assertIsNotNone(view.previous_select)
            self.assertFalse(view.previous_select.disabled)
            self.assertIn("previous grade", view.current_embed().description)

        asyncio.run(scenario())

    def test_dashboard_result_keeps_courses_readable(self) -> None:
        session = CalculatorSession(
            user_id=1001,
            courses=[PlannedCourse(Decimal("3"), "A-")],
        )
        embed = calculator_embed(session)
        self.assertIn("3 credits", embed.fields[3].value)
        self.assertIn("A-", embed.fields[3].value)

    def test_help_uses_navigation_instead_of_full_command_dump(self) -> None:
        async def scenario() -> None:
            view = HelpView(user_id=1001, avatar_url=None)
            self.assertEqual(len(view.children), 3)
            self.assertTrue(any(isinstance(item, discord.ui.Select) for item in view.children))
            embed = help_embed("home", None)
            self.assertIn("/cgpa calculator", embed.description)
            self.assertLess(len(embed.description), 900)
            calculator_help = help_embed("cgpa", None)
            self.assertIn("Add retake", calculator_help.description)
            self.assertIn("Calculate CGPA", calculator_help.description)
            self.assertNotIn("Turn on **Retake**", calculator_help.description)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
