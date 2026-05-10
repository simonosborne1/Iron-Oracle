import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote, parse_qs, urlparse
from models import ManualResult

DDG_URL = "https://html.duckduckgo.com/html/"

TYPE_KEYWORDS = {
    "service": ["service", "repair", "maintenance", "workshop"],
    "parts": ["parts", "illustrated", "ipl"],
    "operator": ["operator", "operation", "user", "owner"],
}


def _classify(title: str) -> str:
    t = title.lower()
    for mtype, keywords in TYPE_KEYWORDS.items():
        if any(k in t for k in keywords):
            return mtype
    return "unknown"


def _extract_url(href: str) -> str:
    if "uddg=" in href:
        parsed = parse_qs(urlparse(href).query)
        return unquote(parsed.get("uddg", [""])[0])
    return href


async def search_manuals(make: str, model: str) -> list[ManualResult]:
    results: list[ManualResult] = []
    seen_urls: set[str] = set()
    queries = [
        f"{make} {model} service manual pdf",
        f"{make} {model} parts manual pdf",
        f"{make} {model} operator manual pdf",
    ]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for query in queries:
            try:
                resp = await client.post(DDG_URL, data={"q": query}, headers=headers)
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.select(".result__a"):
                    href = a.get("href", "")
                    url = _extract_url(href)
                    if not url or url in seen_urls:
                        continue
                    if not (url.lower().endswith(".pdf") or "manual" in url.lower()):
                        continue
                    seen_urls.add(url)
                    title = a.get_text(strip=True) or url
                    results.append(ManualResult(
                        title=title,
                        url=url,
                        manual_type=_classify(title),
                        source="serper",
                    ))
            except Exception:
                continue

    return results
