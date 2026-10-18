"""Registry of the six store adapters. Each of the six exists as its own module."""
from app.scrapers.agora import AgoraScraper
from app.scrapers.chaldal import ChaldalScraper
from app.scrapers.daraz import DarazScraper
from app.scrapers.pickaboo import PickabooScraper
from app.scrapers.rokomari import RokomariScraper
from app.scrapers.shwapno import ShwapnoScraper

SCRAPERS = {s.store: s for s in (DarazScraper(), PickabooScraper(), ChaldalScraper(),
                                 ShwapnoScraper(), AgoraScraper(), RokomariScraper())}


def get_scraper(store: str):
    return SCRAPERS[store]


def all_stores() -> list[str]:
    return list(SCRAPERS)