from decimal import Decimal
import unittest

from services.grading import (
    CourseAttempt,
    calculate_academic_summary,
    grade_for_mark,
    parse_course_rows,
    project_cgpa,
    required_gpa,
)


class GradeScaleTests(unittest.TestCase):
    def test_all_official_boundaries(self) -> None:
        expected = {
            100: ("A", Decimal("4.00")),
            90: ("A", Decimal("4.00")),
            89: ("A-", Decimal("3.67")),
            86: ("A-", Decimal("3.67")),
            85: ("B+", Decimal("3.33")),
            82: ("B+", Decimal("3.33")),
            81: ("B", Decimal("3.00")),
            78: ("B", Decimal("3.00")),
            77: ("B-", Decimal("2.67")),
            74: ("B-", Decimal("2.67")),
            73: ("C+", Decimal("2.33")),
            70: ("C+", Decimal("2.33")),
            69: ("C", Decimal("2.00")),
            66: ("C", Decimal("2.00")),
            65: ("C-", Decimal("1.67")),
            62: ("C-", Decimal("1.67")),
            61: ("D+", Decimal("1.33")),
            58: ("D+", Decimal("1.33")),
            57: ("D", Decimal("1.00")),
            55: ("D", Decimal("1.00")),
            54: ("F", Decimal("0.00")),
            0: ("F", Decimal("0.00")),
        }
        for mark, result in expected.items():
            with self.subTest(mark=mark):
                band = grade_for_mark(mark)
                self.assertEqual((band.grade, band.point), result)

    def test_invalid_mark_rejected(self) -> None:
        with self.assertRaises(ValueError):
            grade_for_mark(101)


class GradeParsingTests(unittest.TestCase):
    def test_csv_and_header(self) -> None:
        parsed = parse_course_rows(
            "term,course,credits,grade\n"
            "261,CSE 1001,3,A-\n"
            "261,ENG 1001,3,B+"
        )
        self.assertEqual(len(parsed.attempts), 2)
        self.assertEqual(parsed.attempts[0].grade, "A-")

    def test_portal_shaped_tab_rows_skip_running_course(self) -> None:
        parsed = parse_course_rows(
            "Trimester\tCourse ID\tCourse Name\tCredit\tGrade\tPoint\tCourse Status\n"
            "261\tCSE 1001\tProgramming\t3\tB\t3.00\t\n"
            "262\tCSE 1002\tAlgorithms\t3\t\t\tRunning Course"
        )
        self.assertEqual(len(parsed.attempts), 1)
        self.assertEqual(len(parsed.warnings), 1)
        self.assertIn("running course", parsed.warnings[0])

    def test_unknown_grade_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown grade"):
            parse_course_rows("CSE 1001,3,Z")

    def test_withdrawn_alias_is_accepted(self) -> None:
        parsed = parse_course_rows("CSE 1001,3,Withdrawn")
        self.assertEqual(parsed.attempts[0].grade, "W")


class AcademicSummaryTests(unittest.TestCase):
    def test_failed_course_counts_in_attempted_but_not_earned_credits(self) -> None:
        summary = calculate_academic_summary(
            (
                CourseAttempt("261", "CSE 1001", Decimal("3"), "F", sequence=0),
                CourseAttempt("261", "ENG 1001", Decimal("3"), "A", sequence=1),
            )
        )
        self.assertEqual(summary.attempted_credits, Decimal("6"))
        self.assertEqual(summary.earned_credits, Decimal("3"))
        self.assertEqual(summary.portal_cgpa, Decimal("2.00"))
        self.assertEqual(summary.transcript_cgpa, Decimal("4.00"))

    def test_latest_graded_retake_replaces_earlier_attempt(self) -> None:
        parsed = parse_course_rows(
            "261,CSE 1001,3,F\n"
            "262,CSE 1001,3,B\n"
            "262,MAT 1001,3,W\n"
            "262,ENG 1001,3,A"
        )
        summary = calculate_academic_summary(parsed.attempts)
        self.assertEqual(summary.replaced_attempts, 1)
        self.assertEqual(summary.withdrawals, 1)
        self.assertEqual(summary.attempted_credits, Decimal("6"))
        self.assertEqual(summary.portal_cgpa, Decimal("3.50"))

    def test_withdrawal_and_incomplete_do_not_replace_prior_grade(self) -> None:
        parsed = parse_course_rows(
            "261,CSE 1001,3,B\n"
            "262,CSE 1001,3,W\n"
            "263,CSE 1001,3,I"
        )
        summary = calculate_academic_summary(parsed.attempts)
        self.assertEqual(summary.portal_cgpa, Decimal("3.00"))
        self.assertEqual(summary.withdrawals, 1)
        self.assertEqual(summary.incompletes, 1)

    def test_non_gpa_rows_alone_cannot_produce_a_cgpa(self) -> None:
        parsed = parse_course_rows("CSE 1001,3,W")
        with self.assertRaisesRegex(ValueError, "A–F"):
            calculate_academic_summary(parsed.attempts)


class ProjectionTests(unittest.TestCase):
    def test_project_cgpa(self) -> None:
        result = project_cgpa(
            Decimal("2.50"), Decimal("30"), Decimal("15"), Decimal("4.00")
        )
        self.assertEqual(result, Decimal("3.00"))

    def test_required_gpa(self) -> None:
        result = required_gpa(
            Decimal("2.50"), Decimal("30"), Decimal("15"), Decimal("3.00")
        )
        self.assertEqual(result, Decimal("4.00"))


if __name__ == "__main__":
    unittest.main()
