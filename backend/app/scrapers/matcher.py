"""Decides whether two product records are the same product. CAUTIOUS by design.

match_type:
  "exact"    same brand AND same model/variant words AND same size/quantity. Safe to compare prices directly.
  "possible" similar, but something differs or is unknown (size, variant, missing brand). Shown with the
             differences listed so the shopper can judge; never presented as identical.
  "none"     different brands, different unit kinds, different categories, or too little in common.
Names that merely look similar are NOT enough for "exact".
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from app.scrapers.normalizer import _UNIT_RE

_STOPWORDS = {"the", "and", "for", "with", "new", "original", "official", "genuine", "bd", "bangladesh", "in", "of",
              "a", "an", "by", "only", "buy", "best", "price"}


def _norm_text(text: str) -> str:
    t = (text or "").lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def identity_tokens(product: dict) -> frozenset[str]:
    """Distinctive name words: brand, sizes (1 kg, 500 g) and filler words removed."""
    text = (product.get("name") or "").lower()
    text = _UNIT_RE.sub(" ", text)                     # sizes are compared separately, not as words
    brand_words = set(_norm_text(product.get("brand") or "").split())
    return frozenset(t for t in _norm_text(text).split() if t not in _STOPWORDS and t not in brand_words)


def model_tokens(tokens) -> frozenset[str]:
    """Words that identify a model/variant: contain a digit (e.g. 'wh1000xm5', '128gb', '15', 'a54')."""
    return frozenset(t for t in tokens if any(c.isdigit() for c in t))


@dataclass
class MatchResult:
    match_type: str                       # "exact" | "possible" | "none"
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    differences: list[dict] = field(default_factory=list)


def _size(p: dict):
    q, u = p.get("quantity"), p.get("unit")
    return (q, u) if q is not None and u else None


def match_products(a: dict, b: dict) -> MatchResult:
    ba, bb = _norm_text(a.get("brand") or ""), _norm_text(b.get("brand") or "")
    diffs: list[dict] = []
    reasons: list[str] = []

    if ba and bb and ba != bb:
        return MatchResult("none", 0.0, ["different brands"])
    ca, cb = a.get("subcategory_slug"), b.get("subcategory_slug")
    if ca and cb and ca != cb:
        return MatchResult("none", 0.0, ["different subcategories"])

    sa, sb = _size(a), _size(b)
    if sa and sb and sa[1] != sb[1]:
        return MatchResult("none", 0.0, ["incomparable units"])

    ta, tb = identity_tokens(a), identity_tokens(b)
    if not ta or not tb:
        return MatchResult("none", 0.0, ["not enough descriptive words"])
    # Similarity uses the descriptive WORDS; model/variant tokens (anything with a digit) are compared separately
    # below, so "A54 128GB" vs "A54 256GB" is a flagged variant difference rather than "unrelated".
    wa = frozenset(t for t in ta if not any(c.isdigit() for c in t))
    wb = frozenset(t for t in tb if not any(c.isdigit() for c in t))
    jaccard = len(wa & wb) / len(wa | wb) if (wa or wb) else len(ta & tb) / len(ta | tb)
    if jaccard < 0.6:
        return MatchResult("none", round(jaccard, 2), ["names share too little"])

    exact = True
    if ba and bb:
        reasons.append("same brand")
    else:
        exact = False
        diffs.append({"field": "brand", "a": a.get("brand"), "b": b.get("brand"), "note": "brand missing on at least one side"})
    if ta == tb:
        reasons.append("same model/variant words")
    else:
        exact = False
        ma, mb = model_tokens(ta), model_tokens(tb)
        if ma != mb:
            diffs.append({"field": "model_or_variant", "a": sorted(ma - mb), "b": sorted(mb - ma)})
        else:
            diffs.append({"field": "name_words", "a": sorted(ta - tb), "b": sorted(tb - ta)})
    if sa and sb:
        if sa == sb:
            reasons.append("same size")
        else:
            exact = False
            diffs.append({"field": "package_size", "a": f"{sa[0]:g} {sa[1]}", "b": f"{sb[0]:g} {sb[1]}"})
    elif sa or sb:
        exact = False
        diffs.append({"field": "package_size", "a": f"{sa[0]:g} {sa[1]}" if sa else None,
                      "b": f"{sb[0]:g} {sb[1]}" if sb else None, "note": "size stated on one side only"})
    return MatchResult("exact" if exact else "possible", round(jaccard, 2), reasons, diffs)


def exact_group_key(product: dict) -> str | None:
    """Stable key shared by products that would match as 'exact'. None if not enough information."""
    brand = _norm_text(product.get("brand") or "")
    tokens = identity_tokens(product)
    if not brand or not tokens:
        return None
    size = _size(product)
    raw = f"{brand}|{' '.join(sorted(tokens))}|{size[0]:g}{size[1] if size else ''}" if size else f"{brand}|{' '.join(sorted(tokens))}|"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]