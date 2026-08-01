"""UIU grading calculations with no Discord or persistence dependencies."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Sequence


UIU_GRADING_SOURCE = (
    "https://www.uiu.ac.bd/academics/grading-performance-evaluation/"
)
UIU_RETAKE_SOURCE = "https://www.uiu.ac.bd/academics/academic-information-policies/"
MINIMUM_CGPA = Decimal("2.00")
MAX_COURSE_ROWS = 80


@dataclass(frozen=True)
class GradeBand:
    grade: str
    point: Decimal
    minimum_mark: int
    maximum_mark: int


GRADE_BANDS: tuple[GradeBand, ...] = (
    GradeBand("A", Decimal("4.00"), 90, 100),
    GradeBand("A-", Decimal("3.67"), 86, 89),
    GradeBand("B+", Decimal("3.33"), 82, 85),
    GradeBand("B", Decimal("3.00"), 78, 81),
    GradeBand("B-", Decimal("2.67"), 74, 77),
    GradeBand("C+", Decimal("2.33"), 70, 73),
    GradeBand("C", Decimal("2.00"), 66, 69),
    GradeBand("C-", Decimal("1.67"), 62, 65),
    GradeBand("D+", Decimal("1.33"), 58, 61),
    GradeBand("D", Decimal("1.00"), 55, 57),
    GradeBand("F", Decimal("0.00"), 0, 54),
)
GRADE_POINTS = {band.grade: band.point for band in GRADE_BANDS}
NON_GPA_GRADES = {"W", "I"}


@dataclass(frozen=True)
class CourseAttempt:
    term: str
    course_code: str
    credits: Decimal
    grade: str
    course_name: str = ""
    sequence: int = 0

    @property
    def grade_point(self) -> Decimal | None:
        return GRADE_POINTS.get(self.grade)

    @property
    def quality_points(self) -> Decimal:
        point = self.grade_point
        return self.credits * point if point is not None else Decimal("0")


@dataclass(frozen=True)
class ParseResult:
    attempts: tuple[CourseAttempt, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class TermResult:
    term: str
    gpa: Decimal | None
    attempted_credits: Decimal
    course_count: int


@dataclass(frozen=True)
class AcademicSummary:
    portal_cgpa: Decimal | None
    transcript_cgpa: Decimal | None
    attempted_credits: Decimal
    earned_credits: Decimal
    quality_points: Decimal
    effective_courses: int
    replaced_attempts: int
    withdrawals: int
    incompletes: int
    term_results: tuple[TermResult, ...]

    @property
    def meets_minimum_cgpa(self) -> bool | None:
        if self.portal_cgpa is None:
            return None
        return self.portal_cgpa >= MINIMUM_CGPA


def round_gpa(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def grade_for_mark(mark: int | Decimal) -> GradeBand:
    try:
        numeric_mark = Decimal(str(mark))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Mark must be a number from 0 to 100.") from exc
    if numeric_mark < 0 or numeric_mark > 100:
        raise ValueError("Mark must be from 0 to 100.")
    for band in GRADE_BANDS:
        if Decimal(band.minimum_mark) <= numeric_mark <= Decimal(band.maximum_mark):
            return band
    raise ValueError("Mark must be a whole-number percentage from 0 to 100.")


def normalize_grade(value: str) -> str:
    grade = value.strip().upper()
    grade = {
        "WITHDRAW": "W",
        "WITHDRAWN": "W",
        "INCOMPLETE": "I",
    }.get(grade, grade)
    if grade not in GRADE_POINTS and grade not in NON_GPA_GRADES:
        raise ValueError(
            f"Unknown grade '{value.strip()}'. Use A through F, W, or I."
        )
    return grade


def normalize_course_code(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().upper())
    if not normalized:
        raise ValueError("Course code cannot be empty.")
    if len(normalized) > 30:
        raise ValueError("Course code is too long (maximum 30 characters).")
    return normalized


def parse_course_rows(text: str) -> ParseResult:
    """Parse course rows without storing the supplied text.

    Supported forms:
      term,course,credits,grade
      course,credits,grade
      term,course,course name,credits,grade,point,status
    Tabs and semicolons may be used instead of commas.
    """

    cleaned = text.strip().replace("```csv", "").replace("```", "")
    if not cleaned:
        raise ValueError("No course rows were provided.")

    raw_lines = [line for line in cleaned.splitlines() if line.strip()]
    attempts: list[CourseAttempt] = []
    warnings: list[str] = []

    for line_number, line in enumerate(raw_lines, start=1):
        row = _split_row(line)
        if _is_header(row):
            continue
        try:
            parsed = _parse_row(row, sequence=len(attempts))
        except _SkipRow as exc:
            warnings.append(f"Line {line_number}: {exc}")
            continue
        except ValueError as exc:
            raise ValueError(f"Line {line_number}: {exc}") from exc
        attempts.append(parsed)
        if len(attempts) > MAX_COURSE_ROWS:
            raise ValueError(f"A maximum of {MAX_COURSE_ROWS} course rows is allowed.")

    if not attempts:
        raise ValueError("No completed course rows were found.")
    return ParseResult(tuple(attempts), tuple(warnings))


def _split_row(line: str) -> list[str]:
    for delimiter in ("\t", ",", ";"):
        if delimiter in line:
            return next(csv.reader(io.StringIO(line), delimiter=delimiter))
    return re.split(r"\s{2,}", line.strip())


def _is_header(row: Sequence[str]) -> bool:
    lowered = " ".join(row).strip().lower()
    return (
        "credit" in lowered
        and "grade" in lowered
        and ("course" in lowered or "subject" in lowered)
    )


class _SkipRow(Exception):
    pass


def _parse_row(row: Sequence[str], sequence: int) -> CourseAttempt:
    fields = [field.strip() for field in row]
    if len(fields) >= 6:
        term, code, name, credit_text, grade_text = (
            fields[0],
            fields[1],
            fields[2],
            fields[3],
            fields[4],
        )
        status = " ".join(fields[6:]).lower() if len(fields) >= 7 else ""
        if not grade_text and "running" in status:
            raise _SkipRow("running course skipped")
    elif len(fields) == 5:
        term, code, name, credit_text, grade_text = fields
    elif len(fields) == 4:
        term, code, credit_text, grade_text = fields
        name = ""
    elif len(fields) == 3:
        code, credit_text, grade_text = fields
        term, name = "Unspecified", ""
    else:
        raise ValueError(
            "expected course,credits,grade or term,course,credits,grade"
        )

    if not grade_text:
        raise _SkipRow("blank grade skipped")

    try:
        credits = Decimal(credit_text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid credit value '{credit_text}'") from exc
    if credits <= 0 or credits > 12:
        raise ValueError("credits must be greater than 0 and no more than 12")

    return CourseAttempt(
        term=term.strip() or "Unspecified",
        course_code=normalize_course_code(code),
        credits=credits,
        grade=normalize_grade(grade_text),
        course_name=name.strip()[:120],
        sequence=sequence,
    )


def calculate_academic_summary(attempts: Iterable[CourseAttempt]) -> AcademicSummary:
    ordered = tuple(attempts)
    if not ordered:
        raise ValueError("At least one course attempt is required.")

    latest_graded: dict[str, CourseAttempt] = {}
    graded_attempt_count = 0
    withdrawals = 0
    incompletes = 0

    for attempt in ordered:
        if attempt.grade in GRADE_POINTS:
            graded_attempt_count += 1
            latest_graded[attempt.course_code] = attempt
        elif attempt.grade == "W":
            withdrawals += 1
        elif attempt.grade == "I":
            incompletes += 1

    effective = tuple(sorted(latest_graded.values(), key=lambda item: item.sequence))
    if not effective:
        raise ValueError("At least one completed course with an A–F grade is required.")
    attempted_credits = sum(
        (attempt.credits for attempt in effective), start=Decimal("0")
    )
    quality_points = sum(
        (attempt.quality_points for attempt in effective), start=Decimal("0")
    )
    earned_credits = sum(
        (
            attempt.credits
            for attempt in effective
            if attempt.grade_point is not None and attempt.grade_point > 0
        ),
        start=Decimal("0"),
    )

    portal_cgpa = (
        round_gpa(quality_points / attempted_credits)
        if attempted_credits
        else None
    )
    transcript_cgpa = (
        round_gpa(quality_points / earned_credits) if earned_credits else None
    )

    return AcademicSummary(
        portal_cgpa=portal_cgpa,
        transcript_cgpa=transcript_cgpa,
        attempted_credits=attempted_credits,
        earned_credits=earned_credits,
        quality_points=quality_points,
        effective_courses=len(effective),
        replaced_attempts=max(0, graded_attempt_count - len(effective)),
        withdrawals=withdrawals,
        incompletes=incompletes,
        term_results=_calculate_term_results(ordered),
    )


def _calculate_term_results(attempts: Sequence[CourseAttempt]) -> tuple[TermResult, ...]:
    grouped: dict[str, list[CourseAttempt]] = {}
    for attempt in attempts:
        grouped.setdefault(attempt.term, []).append(attempt)

    results: list[TermResult] = []
    for term, term_attempts in grouped.items():
        graded = [item for item in term_attempts if item.grade in GRADE_POINTS]
        credits = sum((item.credits for item in graded), start=Decimal("0"))
        points = sum((item.quality_points for item in graded), start=Decimal("0"))
        results.append(
            TermResult(
                term=term,
                gpa=round_gpa(points / credits) if credits else None,
                attempted_credits=credits,
                course_count=len(graded),
            )
        )
    return tuple(results)


def project_cgpa(
    current_cgpa: Decimal,
    completed_credits: Decimal,
    planned_credits: Decimal,
    planned_gpa: Decimal,
) -> Decimal:
    _validate_gpa(current_cgpa, "Current CGPA")
    _validate_gpa(planned_gpa, "Planned GPA")
    _validate_credit_total(completed_credits, "Completed credits", allow_zero=True)
    _validate_credit_total(planned_credits, "Planned credits", allow_zero=False)
    total_credits = completed_credits + planned_credits
    return round_gpa(
        ((current_cgpa * completed_credits) + (planned_gpa * planned_credits))
        / total_credits
    )


def required_gpa(
    current_cgpa: Decimal,
    completed_credits: Decimal,
    planned_credits: Decimal,
    target_cgpa: Decimal,
) -> Decimal:
    _validate_gpa(current_cgpa, "Current CGPA")
    _validate_gpa(target_cgpa, "Target CGPA")
    _validate_credit_total(completed_credits, "Completed credits", allow_zero=True)
    _validate_credit_total(planned_credits, "Planned credits", allow_zero=False)
    required = (
        target_cgpa * (completed_credits + planned_credits)
        - current_cgpa * completed_credits
    ) / planned_credits
    return round_gpa(max(Decimal("0"), required))


def _validate_gpa(value: Decimal, label: str) -> None:
    if value < 0 or value > 4:
        raise ValueError(f"{label} must be from 0.00 to 4.00.")


def _validate_credit_total(value: Decimal, label: str, *, allow_zero: bool) -> None:
    if value < 0 or (not allow_zero and value == 0) or value > 300:
        qualifier = "0 or more" if allow_zero else "greater than 0"
        raise ValueError(f"{label} must be {qualifier} and no more than 300.")
