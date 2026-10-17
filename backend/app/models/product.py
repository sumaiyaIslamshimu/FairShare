"""Shared product contracts. External and FairShare products are DIFFERENT things.

- "external": scraped from another store, comparison-only, lives in `external_products`.
- "fairshare": sold by a FairShare seller, lives in `seller_products`, can be bought.
Only the "fairshare" source may ever enter a cart or order.
"""
from enum import Enum


class ProductSource(str, Enum):
    external = "external"
    fairshare = "fairshare"


class StoreName(str, Enum):
    daraz = "daraz"
    pickaboo = "pickaboo"
    chaldal = "chaldal"
    shwapno = "shwapno"
    agora = "agora"
    rokomari = "rokomari"


class Availability(str, Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"
    unknown = "unknown"


class Freshness(str, Enum):
    fresh = "fresh"
    stale = "stale"
    unavailable = "unavailable"


# Money is stored as integer paisa (BDT x 100) to avoid float rounding errors.
CURRENCY = "BDT"