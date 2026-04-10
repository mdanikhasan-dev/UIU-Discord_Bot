"""
utils/fetch_notices.py
─────────────────────
Fetches the latest notices from the UIU notice board page.

Design decisions:
- requests + BeautifulSoup is kept for HTML parsing (reliable, well-maintained).
- The blocking requests.get() call is offloaded to a thread via
  asyncio.to_thread() so it NEVER blocks the Discord event loop.
- A hard timeout is enforced at the requests level so a slow server
  cannot stall the thread indefinitely.
- Any exception is caught and logged; the caller receives an empty list
  rather than a raised exception, so the background loop never crashes.
"""

import asyncio
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

URL = "https://www.uiu.ac.bd/notice/"
REQUEST_TIMEOUT_SECONDS = 15   # connect + read combined


def _fetch_notices_sync() -> List[Tuple[str, str]]:
    """
    Blocking function — must only be called inside asyncio.to_thread().
    Returns a list of (title, url) tuples for the first 5 notices found.
    """
    response = requests.get(
        URL,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "UIUBot/1.0 (+https://github.com)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    all_notices = soup.find_all("div", class_="details")

    results: List[Tuple[str, str]] = []
    for notice in all_notices[:5]:
        title_container = notice.find("div", class_="title")
        if not title_container:
            continue

        title_tag = title_container.find("a")
        if not title_tag:
            continue

        title_text: str = title_tag.get_text(strip=True)
        title_link: str = title_tag.get("href", "")

        if not title_link:
            continue

        if not title_link.startswith("http"):
            title_link = "https://www.uiu.ac.bd" + title_link

        results.append((title_text, title_link))

    return results


async def fetch_notices() -> List[Tuple[str, str]]:
    """
    Async wrapper around _fetch_notices_sync().
    Runs the blocking HTTP + parsing work in a thread pool executor so
    the Discord gateway heartbeat is never starved.
    """
    try:
        return await asyncio.to_thread(_fetch_notices_sync)
    except requests.exceptions.Timeout:
        print("[fetch_notices] Request timed out.")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"[fetch_notices] Connection error: {e}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[fetch_notices] HTTP error {e.response.status_code}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[fetch_notices] Request failed: {e}")
        return []
    except Exception as e:
        # Catch-all: parsing errors, unexpected issues, etc.
        print(f"[fetch_notices] Unexpected error: {type(e).__name__}: {e}")
        return []
