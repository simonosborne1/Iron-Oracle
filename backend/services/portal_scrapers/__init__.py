from .jlg import JLGScraper
from .genie import GenieScraper
from .skyjack import SkyjackScraper

SCRAPERS = {
    "jlg": JLGScraper,
    "genie": GenieScraper,
    "skyjack": SkyjackScraper,
}


def get_scraper(make: str):
    key = make.lower().strip()
    for name, cls in SCRAPERS.items():
        if name in key:
            return cls()
    return None
