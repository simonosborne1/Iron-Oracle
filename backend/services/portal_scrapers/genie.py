import re
import httpx
from bs4 import BeautifulSoup
from models import ManualResult
from .base import ManualPortalScraper

BASE = "https://manuals.genielift.com/parts%20and%20service%20manuals/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Model prefix regex → category index page on manuals.genielift.com
_CATEGORIES = [
    (r"^SX?[-\s]?\d",            "ServSBoomsIndex.htm"),
    (r"^Z[-\s]?\d",              "ServZBoomsIndex.htm"),
    (r"^GS[-\s]?\d",             "ServScissorsindex.htm"),
    (r"^GTH[-\s]?\d",            "servtelehandlersGTHIndex.htm"),
    (r"^(TH|TX)[-\s]?\d",        "ServTelehandlersIndex.htm"),
    (r"^(QS|IWP|AWP|A)[-\s]?\d", "ServPersonnelLiftsIndex.htm"),
    (r"^TZ[-\s]?\d",             "ServTowedAerial.htm"),
]


class GenieScraper(ManualPortalScraper):

    async def search(self, make: str, model: str, serial: str) -> list[ManualResult]:
        cat_page = self._category_page(model)
        if not cat_page:
            return []

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            sub_pages = await self._get_sub_pages(client, cat_page, model)
            if not sub_pages:
                return []

            results: list[ManualResult] = []
            seen: set[str] = set()
            for page in sub_pages:
                try:
                    resp = await client.get(BASE + page, headers=HEADERS)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for r in self._extract_manuals(soup, model, serial):
                        if r.url not in seen:
                            seen.add(r.url)
                            results.append(r)
                except Exception:
                    continue

        return results

    async def _get_sub_pages(self, client, cat_page: str, model: str) -> list[str]:
        try:
            resp = await client.get(BASE + cat_page, headers=HEADERS)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        model_key = re.sub(r"[^A-Z0-9]", "", model.upper())[:5]
        candidates: list[tuple[int, str]] = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.endswith(".htm") or href.startswith("http") or href == "1MainSMIndex.htm":
                continue
            link_text = a.get_text(strip=True).upper()
            score = 2 if model_key in link_text else 1
            candidates.append((score, href))

        candidates.sort(key=lambda x: -x[0])
        return [p for _, p in candidates]

    def _extract_manuals(self, soup: BeautifulSoup, model: str, serial: str) -> list[ManualResult]:
        results: list[ManualResult] = []
        model_key = re.sub(r"[^A-Z0-9]", "", model.upper())[:5]

        for heading in soup.find_all(["h2", "h3", "h4", "b", "strong"]):
            if model_key not in heading.get_text(strip=True).upper():
                continue

            for sib in heading.find_all_next(["a", "h2", "h3"]):
                if sib.name in ("h2", "h3") and sib != heading:
                    break
                if sib.name != "a" or ".pdf" not in sib.get("href", "").lower():
                    continue

                href = sib["href"]
                full_url = (BASE + href) if not href.startswith("http") else href
                row = sib.find_parent(["tr", "li", "div", "p"]) or sib
                context = row.get_text(separator=" ", strip=True)
                serial_range = self._extract_range(context)

                if serial and serial_range and not self._in_range(serial, serial_range):
                    continue

                manual_type = self.classify(context) or "service"
                title = f"Genie {model} {manual_type.title()} Manual"
                if serial_range:
                    title += f" (S/N {serial_range})"

                results.append(ManualResult(
                    title=title, url=full_url,
                    manual_type=manual_type, source="portal",
                ))

        return results

    def _extract_range(self, text: str) -> str:
        m = re.search(
            r"(?:SN|S/N|SERIAL)?\s*([A-Z0-9][\w-]*)\s*(?:[-–]|to)\s*([A-Z0-9][\w-]*)",
            text, re.IGNORECASE,
        )
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

    def _category_page(self, model: str) -> str | None:
        for pattern, page in _CATEGORIES:
            if re.match(pattern, model.strip(), re.IGNORECASE):
                return page
        return None
