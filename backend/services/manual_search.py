import asyncio
import os
from models import ManualResult
from .serper import search_manuals as serper_search
from .duckduckgo import search_manuals as ddg_search
from .portal_scrapers import get_scraper


async def find_manuals(make: str, model: str, serial: str) -> tuple[list[ManualResult], str]:
    scraper = get_scraper(make)
    web_search = serper_search if os.getenv("SERPER_API_KEY") else ddg_search

    tasks = [web_search(make, model)]
    if scraper:
        tasks.append(scraper.search(make, model, serial))

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    serper_results: list[ManualResult] = []
    portal_results: list[ManualResult] = []

    serper_raw = results_list[0]
    if isinstance(serper_raw, list):
        serper_results = serper_raw

    if len(results_list) > 1:
        portal_raw = results_list[1]
        if isinstance(portal_raw, list):
            portal_results = portal_raw

    # Portal results first (more authoritative), then Serper
    seen_urls: set[str] = set()
    merged: list[ManualResult] = []

    for r in portal_results + serper_results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            merged.append(r)

    merged = merged[:15]
    status = "ok" if merged else "no_results"
    return merged, status
