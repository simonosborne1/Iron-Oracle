import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse
from models import ManualResult
from .base import ManualPortalScraper

DDG_URL = "https://html.duckduckgo.com/html/"
JLG_HOST = "csapps.jlg.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class JLGScraper(ManualPortalScraper):
    async def search(self, make: str, model: str, serial: str) -> list[ManualResult]:
        results: list[ManualResult] = []
        seen: set[str] = set()

        # JLG hosts PDFs publicly on csapps.jlg.com — use site-specific search
        # to find the right folder path (folder names aren't perfectly predictable)
        queries = [
            f'site:{JLG_HOST} "{model}" service manual',
            f'site:{JLG_HOST} "{model}" parts manual',
            f'site:{JLG_HOST} "{model}" operator manual',
        ]

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for query in queries:
                try:
                    resp = await client.post(DDG_URL, data={"q": query}, headers=HEADERS)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.select(".result__a"):
                        url = self._extract_ddg_url(a.get("href", ""))
                        if not url or url in seen:
                            continue
                        if JLG_HOST not in url:
                            continue
                        if not url.lower().endswith(".pdf"):
                            continue
                        # Serial range is embedded in the folder path — extract it
                        serial_range = self._range_from_url(url)
                        if serial and serial_range and not self._in_range(serial, serial_range):
                            continue
                        seen.add(url)
                        title = a.get_text(strip=True) or url
                        if serial_range:
                            title += f" (S/N {serial_range})"
                        results.append(ManualResult(
                            title=title,
                            url=url,
                            manual_type=self.classify(title),
                            source="portal",
                        ))
                except Exception:
                    continue

        return results

    def _extract_ddg_url(self, href: str) -> str:
        if "uddg=" in href:
            parsed = parse_qs(urlparse(href).query)
            return unquote(parsed.get("uddg", [""])[0])
        return href

    def _range_from_url(self, url: str) -> str:
        """JLG folder names embed the serial range: 'SN 0300000100 to 0300065079'."""
        m = re.search(r"SN\s+([A-Z0-9]+)\s+to\s+([A-Z0-9]+)", url, re.IGNORECASE)
        return f"{m.group(1)} - {m.group(2)}" if m else ""

    def _in_range(self, serial: str, range_str: str) -> bool:
        parts = re.split(r"\s*[-–]\s*", range_str)
        if len(parts) != 2:
            return True
        try:
            def digits(s: str) -> int:
                d = re.sub(r"[^0-9]", "", s)
                return int(d) if d else 0
            return digits(parts[0]) <= digits(serial) <= digits(parts[1])
        except Exception:
            return True
