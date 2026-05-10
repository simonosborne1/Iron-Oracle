import httpx
import os
from models import ManualResult

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_URL = "https://google.serper.dev/search"

QUERY_TEMPLATES = [
    '"{make} {model}" "service manual" filetype:pdf',
    '"{make} {model}" "parts manual" filetype:pdf',
    '"{make} {model}" "operator manual" filetype:pdf',
]

TYPE_KEYWORDS = {
    "service": ["service", "repair", "maintenance", "workshop"],
    "parts": ["parts", "illustrated parts", "ipl", "parts list"],
    "operator": ["operator", "operation", "user", "owner"],
}


def _classify(title: str) -> str:
    t = title.lower()
    for mtype, keywords in TYPE_KEYWORDS.items():
        if any(k in t for k in keywords):
            return mtype
    return "unknown"


async def search_manuals(make: str, model: str) -> list[ManualResult]:
    if not SERPER_API_KEY:
        return []

    results: list[ManualResult] = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=15) as client:
        for template in QUERY_TEMPLATES:
            query = template.format(make=make, model=model)
            try:
                resp = await client.post(
                    SERPER_URL,
                    headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                    json={"q": query, "num": 10},
                )
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("organic", []):
                    url = item.get("link", "")
                    if not url or url in seen_urls:
                        continue
                    # Only accept PDF links or known manual portals
                    if not (url.lower().endswith(".pdf") or "manual" in url.lower()):
                        continue
                    seen_urls.add(url)
                    title = item.get("title", url)
                    results.append(ManualResult(
                        title=title,
                        url=url,
                        manual_type=_classify(title),
                        source="serper",
                    ))
            except Exception:
                continue

    return results
