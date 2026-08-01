"""Bounded, cached fetcher for the public UIU notice board."""

from __future__ import annotations

import asyncio
import logging
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


NOTICE_URL = "https://www.uiu.ac.bd/notice/"
REQUEST_TIMEOUT = (5, 15)
CACHE_SECONDS = 120
MAX_NOTICES = 5

logger = logging.getLogger(__name__)
_cache_lock = asyncio.Lock()
_cache_time = 0.0
_cache_items: tuple[tuple[str, str], ...] = ()


def _fetch_notices_sync() -> tuple[tuple[str, str], ...]:
    response = requests.get(
        NOTICE_URL,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "UIUBot/2.0 (public notice reader)"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    results: list[tuple[str, str]] = []
    for notice in soup.find_all("div", class_="details"):
        title_container = notice.find("div", class_="title")
        title_tag = title_container.find("a") if title_container else None
        if not title_tag:
            continue
        title = " ".join(title_tag.get_text(" ", strip=True).split())
        href = title_tag.get("href")
        if not title or not isinstance(href, str):
            continue
        link = urljoin(NOTICE_URL, href)
        parsed = urlparse(link)
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith("uiu.ac.bd"):
            continue
        results.append((title[:256], link))
        if len(results) >= MAX_NOTICES:
            break
    return tuple(results)


async def fetch_notices(*, force_refresh: bool = False) -> list[tuple[str, str]]:
    global _cache_items, _cache_time
    now = time.monotonic()
    if not force_refresh and _cache_items and now - _cache_time < CACHE_SECONDS:
        return list(_cache_items)

    async with _cache_lock:
        now = time.monotonic()
        if not force_refresh and _cache_items and now - _cache_time < CACHE_SECONDS:
            return list(_cache_items)
        try:
            items = await asyncio.to_thread(_fetch_notices_sync)
        except requests.exceptions.Timeout:
            logger.warning("UIU notice request timed out")
            return list(_cache_items)
        except requests.exceptions.RequestException as exc:
            logger.warning("UIU notice request failed: %s", type(exc).__name__)
            return list(_cache_items)
        except Exception:
            logger.exception("UIU notice response could not be parsed")
            return list(_cache_items)
        if items:
            _cache_items = items
            _cache_time = time.monotonic()
        return list(items)
