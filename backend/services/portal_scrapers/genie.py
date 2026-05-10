import httpx
from bs4 import BeautifulSoup
from models import ManualResult
from .base import ManualPortalScraper

BASE_URL = "https://www.genielift.com/en/resource-library"


class GenieScraper(ManualPortalScraper):
    async def search(self, make: str, model: str, serial: str) -> list[ManualResult]:
        results: list[ManualResult] = []
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    BASE_URL,
                    params={"q": model, "type": "technical"},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; IronOracle/1.0)"},
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if not href.lower().endswith(".pdf"):
                        continue
                    url = href if href.startswith("http") else f"https://www.genielift.com{href}"
                    title = a.get_text(strip=True) or url
                    if model.lower() not in title.lower() and model.lower() not in url.lower():
                        continue
                    results.append(ManualResult(
                        title=title, url=url,
                        manual_type=self.classify(title), source="portal",
                    ))
        except Exception:
            pass
        return results
