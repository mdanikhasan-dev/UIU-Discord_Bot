import asyncio

import requests
from bs4 import BeautifulSoup

URL = 'https://www.uiu.ac.bd/notice/'
REQUEST_TIMEOUT_SECONDS = 10


def _fetch_notices_sync():
    page = requests.get(URL, timeout=REQUEST_TIMEOUT_SECONDS)
    page.raise_for_status()

    soup = BeautifulSoup(page.content, 'html.parser')
    all_notices = soup.find_all('div', class_='details')

    results = []
    for notice in all_notices[:5]:
        title_container = notice.find('div', class_='title')
        if not title_container:
            continue

        title_tag = title_container.find('a')
        if not title_tag:
            continue

        title_text = title_tag.text.strip()
        title_link = title_tag['href']

        if not title_link.startswith('http'):
            title_link = 'https://www.uiu.ac.bd' + title_link

        results.append((title_text, title_link))

    return results


async def fetch_notices():
    try:
        return await asyncio.to_thread(_fetch_notices_sync)
    except requests.exceptions.RequestException as e:
        print(f'Error fetching website: {e}')
        return []
