import re
import httpx
from bs4 import BeautifulSoup
from models import ManualResult
from .base import ManualPortalScraper

SEARCH_URL = "https://techpub.skyjack.com/doc-search"
PORTAL_BASE = "https://techpub.skyjack.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class SkyjackScraper(ManualPortalScraper):
    async def search(self, make: str, model: str, serial: str) -> list[ManualResult]:
        results: list[ManualResult] = []
        seen_ids: set[str] = set()

        # Serial search first — Skyjack's portal filters to the exact serial range.
        # Model search as fallback if serial returns nothing.
        queries = [q for q in [serial, model] if q]

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for query in queries:
                try:
                    resp = await client.get(
                        SEARCH_URL,
                        params={"s": query, "region": "NA", "language": "en", "doc_type": ""},
                        headers=HEADERS,
                    )
                    resp.raise_for_status()
                    new = self._parse(resp.text, model, seen_ids)
                    results.extend(new)
                    if results:
                        break  # serial search found results, skip model fallback
                except Exception:
                    continue

        return results

    def _parse(self, html: str, model: str, seen_ids: set[str]) -> list[ManualResult]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[ManualResult] = []
        current_type = "unknown"

        for el in soup.find_all(["h2", "h4", "a"]):
            if el.name == "h2":
                current_type = self.classify(el.get_text(strip=True))

            elif el.name == "h4":
                # h4 within a section gives the specific document type label
                current_type = self.classify(el.get_text(strip=True)) or current_type

            elif el.name == "a":
                href = el.get("href", "")
                if "/document/" not in href:
                    continue

                m = re.search(r"id=([A-Z0-9]+)", href)
                part_id = m.group(1) if m else href
                if part_id in seen_ids:
                    continue
                seen_ids.add(part_id)

                full_url = f"{PORTAL_BASE}{href}" if href.startswith("/") else href

                # Pull serial range and doc label from surrounding block
                block = el.find_parent(["div", "section", "article", "li", "td"])
                serial_range = ""
                doc_label = el.get_text(strip=True)
                if block:
                    text = block.get_text(separator=" ")
                    h4 = block.find("h4") or el.find_previous("h4")
                    if h4:
                        doc_label = h4.get_text(strip=True)
                    sr = re.search(r"Serial Range[:\s]+([0-9A-Z][\w\s\-]+)", text)
                    if sr:
                        serial_range = sr.group(1).strip()

                manual_type = self.classify(doc_label) or current_type
                title = f"Skyjack {model} {doc_label}".strip()
                if serial_range:
                    title += f" (S/N {serial_range})"

                results.append(ManualResult(
                    title=title,
                    url=full_url,
                    manual_type=manual_type,
                    source="portal",
                ))

        return results
