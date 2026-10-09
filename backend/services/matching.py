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