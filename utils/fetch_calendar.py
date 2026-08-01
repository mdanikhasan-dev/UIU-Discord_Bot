"""Verified calendar snapshot for the current UIU undergraduate trimester."""

from __future__ import annotations


CALENDAR_SOURCE = (
    "https://www.uiu.ac.bd/academics/calendar/"
    "summer-2026-trimester-undergraduate-programs/"
)

CURRENT_CALENDAR = {
    "semester_title": "Summer 2026 Trimester · Undergraduate Programs",
    "verified_on": "2026-08-01",
    "source_url": CALENDAR_SOURCE,
    "events": [
        {"date": "Aug 5, 2026", "description": "Holiday: July Mass Uprising Day"},
        {"date": "Aug 11, 2026", "description": "Last date of 1st installment"},
        {"date": "Aug 18, 2026", "description": "Regular Saturday classes"},
        {"date": "Aug 22–29, 2026", "description": "Mid-term exam"},
        {"date": "Aug 26, 2026", "description": "Holiday: Eid-e-Miladunnabi"},
        {"date": "Sep 4, 2026", "description": "Holiday: Janmashtami"},
        {"date": "Sep 9, 2026", "description": "Last day of course withdrawal"},
        {"date": "Sep 15, 2026", "description": "Last date of 2nd installment"},
        {"date": "Sep 24, 2026", "description": "Regular Wednesday classes"},
        {"date": "Oct 6, 2026", "description": "Last date of 3rd installment"},
        {"date": "Oct 7–9, 2026", "description": "Classes remain suspended"},
        {"date": "Oct 10–17, 2026", "description": "Final exam"},
        {"date": "Oct 20–21, 2026", "description": "Holiday: Durga Puja"},
        {"date": "Oct 22, 2026", "description": "Last day of grade submission"},
    ],
}


async def fetch_academic_calendar() -> dict:
    return CURRENT_CALENDAR
