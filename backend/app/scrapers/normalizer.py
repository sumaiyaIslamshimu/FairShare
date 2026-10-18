"""Turns a RawProduct into the common normalized record. Never guesses:
bad or ambiguous values become None, and records missing required fields are rejected with a reason."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from app.scrapers.base import RawProduct

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_CURRENCY_MARKERS = {"৳": "BDT", "tk": "BDT", "tk.": "BDT", "bdt": "BDT", "taka": "BDT"}


class InvalidProduct(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _number_from_text(text: str) -> Decimal | None:
    """One clean number from text like '৳ 1,23,456.50'. Several different numbers (ranges, 'was/now') -> None."""
    s = text.translate(_BN_DIGITS)
    if re.search(r"(?:^|[\s৳:])-\s*\d", s):  # a minus sign in front of a number (negative or range) is never a price
        return None
    matches = re.findall(r"\d[\d,]*(?:\.\d+)?", s)
    values = []
    for m in matches:
        try:
            values.append(Decimal(m.replace(",", "")))
        except InvalidOperation:
            return None
    if len(values) != 1:
        return None
    return values[0]


def parse_price_to_paisa(value) -> int | None:
    """Integer paisa (BDT x 100), or None if missing, malformed, zero/negative, or ambiguous."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        dec = Decimal(str(value))
    else:
        dec = _number_from_text(str(value))
    if dec is None or dec <= 0:
        return None
    return int((dec * 100).quantize(Decimal("1")))


def detect_currency(raw_currency, *price_values) -> str | None:
    """'BDT' only when confirmed by the page (currency field or a symbol in the price text)."""
    candidates = [raw_currency] + [v for v in price_values if isinstance(v, str)]
    for c in candidates:
        if not c:
            continue
        low = str(c).strip().lower()
        if low in _CURRENCY_MARKERS:
            return _CURRENCY_MARKERS[low]
        for marker, code in _CURRENCY_MARKERS.items():
            if marker in low.split() or (marker == "৳" and "৳" in low):
                return code
    return None


def normalize_availability(value) -> str:
    if not value:
        return "unknown"
    low = str(value).strip().lower().replace("_", " ")
    if "outofstock" in low.replace(" ", "") or "out of stock" in low or "sold out" in low or "unavailable" in low:
        return "out_of_stock"
    if "instock" in low.replace(" ", "") or "in stock" in low or "available" in low:
        return "in_stock"
    return "unknown"


_UNIT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g|gm|l|ltr|liter|litre|ml|pcs|pc|piece|pieces|pack)\b", re.I)
_UNIT_MAP = {"kg": ("g", 1000), "g": ("g", 1), "gm": ("g", 1), "l": ("ml", 1000), "ltr": ("ml", 1000),
             "liter": ("ml", 1000), "litre": ("ml", 1000), "ml": ("ml", 1), "pcs": ("pcs", 1), "pc": ("pcs", 1),
             "piece": ("pcs", 1), "pieces": ("pcs", 1), "pack": ("pack", 1)}


def parse_quantity_unit(name: str) -> tuple[float, str] | None:
    """('500 g' | '1 kg' -> (500.0/1000.0, 'g')). Units are converted to g / ml / pcs so sizes compare fairly.
    Returns None when no size is stated or when several different sizes appear (ambiguous)."""
    found = {(float(q) * _UNIT_MAP[u.lower()][1], _UNIT_MAP[u.lower()][0]) for q, u in _UNIT_RE.findall(name or "")}
    return found.pop() if len(found) == 1 else None


def canonical_url(url: str | None, base_url: str = "") -> str | None:
    """Absolute http(s) URL without fragment and tracking params. None if not a usable URL."""
    if not url or not isinstance(url, str):
        return None
    joined = urljoin(base_url, url.strip())
    p = urlparse(joined)
    if p.scheme not in ("http", "https") or not p.netloc:
        return None
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid", "spm", "scm")]
    return urlunparse((p.scheme, p.netloc.lower(), p.path, "", urlencode(query), ""))


def _clean_text(value) -> str | None:
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value)).strip()
    return s or None


def _to_float(value) -> float | None:
    try:
        f = float(str(value).translate(_BN_DIGITS).replace(",", "").strip())
    except (ValueError, TypeError):
        return None
    return f if f >= 0 else None


def make_normalized_key(brand: str | None, name: str) -> str:
    text = f"{brand or ''} {name}".lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class NormalizedProduct:
    store: str
    store_product_id: str | None
    name: str
    brand: str | None
    price_paisa: int
    original_price_paisa: int | None
    discount_percent: float | None
    currency: str | None            # "BDT" only if confirmed; None otherwise
    image_url: str | None
    product_url: str
    category_text: str | None       # mapped to a taxonomy slug later by category_map
    availability: str
    rating: float | None
    review_count: int | None
    quantity: float | None
    unit: str | None
    normalized_key: str
    source: str
    scraped_at: datetime

    def as_dict(self) -> dict:
        return asdict(self)


def normalize_product(raw: RawProduct, base_url: str = "", now: datetime | None = None) -> NormalizedProduct:
    """Raises InvalidProduct(reason) when a required field (name, URL, price) is missing or unusable."""
    name = _clean_text(raw.name)
    if not name:
        raise InvalidProduct("missing_name")
    url = canonical_url(raw.product_url, base_url)
    if not url:
        raise InvalidProduct("missing_or_invalid_url")
    price = parse_price_to_paisa(raw.price)
    if price is None:
        raise InvalidProduct("missing_or_invalid_price")
    original = parse_price_to_paisa(raw.original_price)
    discount = None
    if original is not None and original > price:  # only a genuine crossed-out price counts
        discount = round((original - price) / original * 100, 1)
    else:
        original = None
    image = raw.image_url
    if isinstance(image, str) and image.startswith("//"):
        image = "https:" + image
    image = canonical_url(image, base_url) if image else None
    qty = parse_quantity_unit(name)
    brand = _clean_text(raw.brand)
    review = _to_float(raw.review_count)
    return NormalizedProduct(
        store=raw.store,
        store_product_id=_clean_text(raw.store_product_id),
        name=name,
        brand=brand,
        price_paisa=price,
        original_price_paisa=original,
        discount_percent=discount,
        currency=detect_currency(raw.currency, raw.price),
        image_url=image,
        product_url=url,
        category_text=_clean_text(raw.category_text),
        availability=normalize_availability(raw.availability),
        rating=_to_float(raw.rating),
        review_count=int(review) if review is not None else None,
        quantity=qty[0] if qty else None,
        unit=qty[1] if qty else None,
        normalized_key=make_normalized_key(brand, name),
        source="external",
        scraped_at=now or datetime.now(timezone.utc),
    )