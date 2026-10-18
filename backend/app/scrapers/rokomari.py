"""Rokomari adapter.

STATUS: NOT CONFIGURED. No page of this store has been inspected yet, so no URL pattern or selector is claimed.
To configure (on a machine with internet, using a public page you can open in a normal browser):
    python -m app.scrapers.recon "<a public search/listing page URL>" --save rokomari
Then set base_url, search_url_template, verified_on below from that report. If the page has no JSON-LD
Product data, replace parse_listing() with a parser written against the saved fixture in tests/fixtures/rokomari/.
Respect robots.txt and the site terms; a 403/429/captcha means "failure/unsupported", never a workaround.
"""
from app.scrapers.base import JsonLdSearchScraper


class RokomariScraper(JsonLdSearchScraper):
    store = "rokomari"
    base_url = ""                # fill from recon report, e.g. "https://<host>"
    search_url_template = ""     # fill from recon report, must contain {query} (and optionally {page})
    verified_on = ""             # e.g. "2026-10-25"
    extraction_method = "unverified"