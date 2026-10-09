import re


def generate_normalized_key(name: str, brand: str = "", model: str = "") -> str:
    """
    Builds a normalized key for product matching by converting to lowercase,
    removing punctuation, stripping filler words, and sorting the words alphabetically.
    """
    raw_string = f"{name or ''} {brand or ''} {model or ''}".lower()
    no_punctuation = re.sub(r'[^\w\s]', '', raw_string)
    words = no_punctuation.split()

    fillers = {"new", "original", "authentic", "genuine", "sealed", "box"}
    filtered_words = [word for word in words if word not in fillers]

    sorted_words = sorted(list(set(filtered_words)))
    return " ".join(sorted_words)


# ... (Keep your existing generate_normalized_key function at the top) ...

def calculate_word_overlap(key1: str, key2: str) -> float:
    """Calculates the percentage of overlapping words between two keys."""
    set1 = set(key1.split())
    set2 = set(key2.split())

    if not set1 or not set2:
        return 0.0

    # Use the max length to ensure a strict 80% overlap relative to the longer title
    return len(set1 & set2) / max(len(set1), len(set2))


def are_products_matching(p1: dict, p2: dict) -> bool:
    """
    Evaluates if two product dictionaries are the same underlying product.
    """
    key1 = p1.get("normalized_key", "")
    key2 = p2.get("normalized_key", "")

    # Condition 1: Exact normalized key match
    if key1 and key1 == key2:
        return True

    # Condition 2: Same brand + 80% word overlap
    brand1 = (p1.get("brand") or "").strip().lower()
    brand2 = (p2.get("brand") or "").strip().lower()

    if brand1 and brand2 and brand1 == brand2:
        overlap = calculate_word_overlap(key1, key2)
        if overlap >= 0.8:
            return True

    return False