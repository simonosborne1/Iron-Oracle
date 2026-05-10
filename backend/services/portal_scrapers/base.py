from abc import ABC, abstractmethod
from models import ManualResult

TYPE_KEYWORDS = {
    "service": ["service", "repair", "maintenance", "workshop"],
    "parts": ["parts", "illustrated parts", "ipl", "parts list"],
    "operator": ["operator", "operation", "user", "owner"],
}


class ManualPortalScraper(ABC):
    @abstractmethod
    async def search(self, make: str, model: str, serial: str) -> list[ManualResult]:
        ...

    def classify(self, title: str) -> str:
        t = title.lower()
        for mtype, keywords in TYPE_KEYWORDS.items():
            if any(k in t for k in keywords):
                return mtype
        return "unknown"

    def is_valid_pdf_url(self, url: str) -> bool:
        return url.startswith("http") and (
            url.lower().endswith(".pdf") or "pdf" in url.lower()
        )
