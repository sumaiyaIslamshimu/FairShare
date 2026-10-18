"""Maps a scraped product to the FairShare taxonomy (app/db/taxonomy.py) CONSERVATIVELY.

- Uses the source's own category text first (most reliable). The product name alone is never trusted
  enough to publish a category: it only produces a *suggestion* with status "needs_review".
- The most specific (longest) matching keyword wins; a tie between different subcategories, or no match,
  means "needs_review" so an admin decides. Nothing is forced into a broad bucket.
- The keyword lists are generic English product vocabulary, NOT facts about any particular store.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.db.taxonomy import TAXONOMY, subcategory_parent


def _norm(text: str) -> str:
    t = (text or "").lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


_RAW_RULES: dict[str, list[str]] = {
    # --- Fashion & Accessories ---
    "mens-clothing": ["mens clothing", "men clothing", "mens wear", "menswear", "mens fashion", "panjabi",
                      "polo shirt", "mens shirt", "mens t shirt", "mens pant", "mens jeans"],
    "womens-clothing": ["womens clothing", "women clothing", "womens wear", "womenswear", "womens fashion", "saree",
                        "kurti", "salwar kameez", "womens dress", "ladies wear", "ladies clothing", "burqa"],
    "kids-clothing": ["kids clothing", "kids wear", "kids fashion", "baby clothing", "baby clothes", "boys clothing",
                      "girls clothing", "childrens clothing", "kids dress"],
    "shoes-footwear": ["shoes", "shoe", "footwear", "sandals", "sneakers", "boots", "loafers", "slippers", "flip flops"],
    "bags-backpacks": ["bags", "bag", "backpack", "backpacks", "handbag", "handbags", "travel bag", "school bag",
                       "laptop bag"],  # "laptop bag" is deliberately in two subcategories -> always reviewed
    "watches-jewelry": ["watches", "watch", "wrist watch", "jewelry", "jewellery", "necklace", "earrings", "bracelet"],
    "sunglasses-accessories": ["sunglasses", "sunglass", "eyewear", "fashion accessories", "belt", "wallet", "scarf"],
    # --- Electronics & Gadgets ---
    "smartphones-tablets": ["smartphone", "mobile phone", "mobiles", "phones", "tablet", "ipad", "android phone",
                            "feature phone"],
    "laptops-computers": ["laptop", "desktop", "desktop computer", "computers", "pc", "all in one pc", "macbook",
                          "chromebook"],
    "headphones-speakers": ["headphone", "earphone", "earbuds", "earbud", "speaker", "bluetooth speaker", "soundbar",
                            "headset", "airpods"],
    "cameras-photography": ["camera", "dslr", "mirrorless", "lens", "tripod", "gopro", "action camera"],
    "smartwatches-wearables": ["smartwatch", "smart watch", "fitness band", "fitness tracker", "wearable", "smart band"],
    "computer-accessories": ["keyboard", "mouse", "monitor", "usb", "hard drive", "ssd", "pen drive", "flash drive",
                             "router", "webcam", "mouse pad", "laptop bag", "laptop stand", "computer accessories",
                             "printer"],
    "gaming-devices-accessories": ["gaming console", "playstation", "ps5", "ps4", "xbox", "nintendo", "gamepad",
                                   "game controller", "joystick", "gaming headset", "gaming mouse", "gaming keyboard",
                                   "gaming chair", "video game"],
    # --- Home & Household ---
    "kitchenware-cookware": ["cookware", "kitchenware", "frying pan", "fry pan", "pan", "pot", "cooking pot",
                             "saucepan", "kadai", "pressure cooker", "non stick", "utensil", "cutlery", "knife",
                             "knives", "plate", "dinner set", "lunch box", "tiffin", "kettle"],
    "home-decor": ["home decor", "home decoration", "decor", "wall art", "wall decor", "wall clock", "photo frame",
                   "frame", "vase", "showpiece", "artificial flower", "candle", "curtain", "carpet", "rug"],
    "cleaning-supplies": ["cleaning", "detergent", "dishwash", "dish wash", "floor cleaner", "toilet cleaner",
                          "bleach", "broom", "mop", "sponge", "cleaning supplies", "laundry", "disinfectant",
                          "air freshener"],
    "storage-organization": ["storage", "organizer", "organiser", "organization", "shelf", "shelves", "rack",
                             "storage box", "basket", "container", "wardrobe", "drawer", "hanger"],
    "home-appliances": ["refrigerator", "fridge", "washing machine", "microwave", "oven", "air conditioner",
                        "fan", "ceiling fan", "blender", "juicer", "rice cooker", "electric kettle", "electric iron",
                        "steam iron", "vacuum cleaner", "water purifier", "geyser", "heater", "air fryer",
                        "induction cooker", "gas stove", "stove", "home appliances", "television", "tv", "led tv",
                        "smart tv", "coffee maker"],
    "lighting-fixtures": ["light", "lighting", "lamp", "led bulb", "bulb", "chandelier", "tube light",
                          "ceiling light", "wall light", "table lamp", "fixture", "night lamp"],
    "bedding-bath": ["bedding", "bed sheet", "bedsheet", "pillow", "blanket", "comforter", "quilt", "mattress",
                     "towel", "bath mat", "shower curtain", "bathroom accessories", "duvet", "kantha"],
    # --- Groceries & Food ---
    "fruits-vegetables": ["fruit", "vegetable", "fresh fruits", "fresh vegetables", "produce", "fresh produce",
                          "leafy greens", "potato", "onion"],
    "rice-pulses-grains": ["rice", "pulses", "pulse", "lentil", "dal", "daal", "grains", "grain", "atta", "flour",
                           "wheat", "oats", "chira", "muri", "miniket", "basmati", "chickpea"],
    "meat-fish-seafood": ["meat", "chicken", "beef", "mutton", "fish", "seafood", "prawn", "shrimp", "hilsa",
                          "ilish", "lamb"],
    "dairy-eggs": ["dairy", "milk", "egg", "butter", "cheese", "yogurt", "yoghurt", "curd", "ghee", "cream",
                   "paneer", "milk powder"],
    "snacks-sweets": ["snacks", "snack", "chips", "biscuit", "cookies", "cookie", "chocolate", "candy", "sweets",
                      "sweet", "cake", "ice cream", "wafer", "nuts", "dry fruits", "popcorn", "chanachur", "mithai",
                      "dessert", "potato chips"],
    "beverages": ["beverage", "drink", "juice", "tea", "coffee", "soft drink", "soda", "drinking water",
                  "mineral water", "bottled water", "energy drink", "cola"],
    "spices-cooking-essentials": ["spice", "masala", "cooking oil", "soybean oil", "mustard oil", "sunflower oil",
                                  "salt", "sugar", "turmeric", "cumin", "sauce", "ketchup", "vinegar",
                                  "baking powder", "cooking essentials"],
    "packaged-frozen-food": ["frozen food", "frozen", "packaged food", "canned food", "noodles", "instant noodles",
                             "pasta", "cereal", "cornflakes", "jam", "pickle", "ready to eat", "instant food", "soup",
                             "canned", "nuggets"],
    # --- Books & Stationery ---
    "academic-textbooks": ["textbook", "text book", "academic", "academic books", "hsc", "ssc", "admission",
                           "university books", "engineering books", "medical books", "question bank",
                           "job preparation", "bcs"],
    "fiction-non-fiction-books": ["novel", "fiction", "non fiction", "nonfiction", "story book", "storybook",
                                  "poetry", "biography", "self help", "history book", "comics", "literature",
                                  "thriller", "fantasy", "childrens books"],
    "notebooks-paper": ["notebook", "diary", "paper", "a4 paper", "copy paper", "notepad", "sticky notes", "khata",
                        "exercise book", "graph paper"],
    "pens-writing-supplies": ["pen", "pencil", "marker", "highlighter", "eraser", "sharpener", "ink", "ballpoint",
                              "gel pen", "fountain pen", "writing supplies", "correction tape"],
    "office-supplies": ["office supplies", "stapler", "staples", "paper clip", "clips", "file folder", "folder",
                        "envelope", "tape", "glue", "scissors", "punch", "whiteboard", "desk organizer"],
    "art-craft-supplies": ["art supplies", "craft", "paint", "watercolor", "watercolour", "acrylic", "brush",
                           "canvas", "sketchbook", "sketch book", "drawing", "crayon", "clay", "origami",
                           "colour pencil", "color pencil"],
    "calculators-educational-tools": ["calculator", "scientific calculator", "geometry box", "compass", "protractor",
                                      "ruler", "educational", "educational toys", "globe", "abacus", "flash cards",
                                      "math kit", "microscope"],
    # --- Sports & Fitness ---
    "gym-fitness-equipment": ["gym", "dumbbell", "barbell", "kettlebell", "treadmill", "weight plates", "weights",
                              "exercise bike", "resistance band", "bench press", "fitness equipment", "push up",
                              "skipping rope", "jump rope", "ab roller", "gym equipment"],
    "sportswear-shoes": ["sportswear", "sports wear", "sports shoes", "running shoes", "training shoes", "track suit",
                         "tracksuit", "jersey", "gym wear", "activewear", "sports bra", "joggers",
                         "football jersey", "cricket jersey"],
    "football-cricket-equipment": ["football", "cricket", "cricket bat", "cricket ball", "cricket kit", "shin guard",
                                   "football boots", "goalkeeper gloves", "stumps", "batting gloves"],
    "badminton-tennis-equipment": ["badminton", "racket", "racquet", "shuttlecock", "tennis", "tennis ball",
                                   "table tennis", "squash", "badminton racket"],
    "yoga-exercise-accessories": ["yoga", "yoga mat", "exercise mat", "pilates", "foam roller", "yoga block",
                                  "fitness mat", "stretching", "exercise accessories"],
    "cycling-equipment": ["cycle", "bicycle", "cycling", "cycle helmet", "bike helmet", "bicycle pump",
                          "mountain bike", "cycle lock", "bicycle lock"],
    "outdoor-camping-gear": ["camping", "tent", "sleeping bag", "hiking", "trekking", "outdoor", "backpacking",
                             "camping gear", "binoculars", "fishing", "hammock", "survival", "lantern",
                             "trekking pole"],
}

# Compile once. A keyword matches whole words only, with an optional plural ending.
_RULES: list[tuple[str, str, re.Pattern]] = []
for _sub, _kws in _RAW_RULES.items():
    assert subcategory_parent(_sub) is not None, f"rule for unknown subcategory: {_sub}"
    for _kw in _kws:
        _n = _norm(_kw)
        _RULES.append((_sub, _n, re.compile(r"(?<![a-z0-9])" + re.escape(_n) + r"(?:s|es)?(?![a-z0-9])")))


@dataclass
class CategoryMapping:
    status: str                                  # "mapped" | "needs_review"
    category_slug: str | None = None             # only set when status == "mapped"
    subcategory_slug: str | None = None          # only set when status == "mapped"
    suggested_subcategory_slug: str | None = None
    candidates: list[str] = field(default_factory=list)
    reason: str = ""


def _best(text: str) -> tuple[list[str], int]:
    """Subcategories tied for the longest matching keyword in `text`, and that keyword length."""
    t = _norm(text)
    if not t:
        return [], 0
    best_len, winners = 0, set()
    for sub, kw, pat in _RULES:
        if pat.search(t):
            if len(kw) > best_len:
                best_len, winners = len(kw), {sub}
            elif len(kw) == best_len:
                winners.add(sub)
    return sorted(winners), best_len


def map_category(category_text: str | None, name: str | None = None) -> CategoryMapping:
    """status "mapped" only when the SOURCE category text points to exactly one subcategory."""
    from_text, _ = _best(category_text or "")
    if len(from_text) == 1:
        sub = from_text[0]
        return CategoryMapping("mapped", subcategory_parent(sub), sub, sub, from_text, "unique match on source category text")
    if len(from_text) > 1:
        return CategoryMapping("needs_review", candidates=from_text, reason="source category matches several subcategories equally")
    from_name, _ = _best(name or "")
    if len(from_name) == 1:
        return CategoryMapping("needs_review", suggested_subcategory_slug=from_name[0], candidates=from_name,
                               reason="source category missing/unrecognized; suggestion based on product name only")
    if len(from_name) > 1:
        return CategoryMapping("needs_review", candidates=from_name, reason="product name matches several subcategories equally")
    return CategoryMapping("needs_review", reason="no confident match")