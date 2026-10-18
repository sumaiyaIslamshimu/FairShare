from app.db.taxonomy import TAXONOMY, subcategory_parent
from app.scrapers.category_map import map_category

EXPECTED_SUBCOUNTS = {"fashion-accessories": 7, "electronics-gadgets": 7, "home-household": 7,
                      "groceries-food": 8, "books-stationery": 7, "sports-fitness": 7}


def test_taxonomy_is_exactly_the_agreed_six_categories_and_43_subcategories():
    assert {k: len(v[1]) for k, v in TAXONOMY.items()} == EXPECTED_SUBCOUNTS
    all_subs = [s for _, subs in TAXONOMY.values() for s in subs]
    assert len(all_subs) == len(set(all_subs)) == 43            # slugs are unique, so they work as stable IDs
    assert subcategory_parent("mens-clothing") == "fashion-accessories"
    assert subcategory_parent("nope") is None


def test_source_category_text_maps_to_exact_subcategory():
    cases = {"Mobiles": "smartphones-tablets", "Smart Watches": "smartwatches-wearables",
             "Men's Clothing": "mens-clothing", "Gaming Mouse": "gaming-devices-accessories",
             "Electronics > Gaming > Gaming Mouse": "gaming-devices-accessories",
             "Dumbbells": "gym-fitness-equipment", "Bed Sheets": "bedding-bath",
             "Instant Noodles": "packaged-frozen-food", "Scientific Calculator": "calculators-educational-tools"}
    for text, sub in cases.items():
        r = map_category(text)
        assert r.status == "mapped" and r.subcategory_slug == sub, (text, r)
        assert r.category_slug == subcategory_parent(sub)


def test_specific_keyword_beats_general_one():
    assert map_category("Rice Cooker").subcategory_slug == "home-appliances"      # not Rice, Pulses & Grains
    assert map_category("Football Jerseys").subcategory_slug == "sportswear-shoes"  # not Football & Cricket
    assert map_category("Mouse Pad").subcategory_slug == "computer-accessories"


def test_ambiguous_goes_to_review_not_guessed():
    r = map_category("Laptop Bag")                                   # Bags AND Computer Accessories
    assert r.status == "needs_review" and r.subcategory_slug is None
    assert set(r.candidates) == {"bags-backpacks", "computer-accessories"}


def test_name_alone_only_suggests():
    r = map_category(None, "Miniket Rice 5 kg")
    assert r.status == "needs_review" and r.category_slug is None and r.subcategory_slug is None
    assert r.suggested_subcategory_slug == "rice-pulses-grains"


def test_unknown_or_empty_is_review():
    for args in [("Home", "z"), (None, None), ("", ""), ("Misc", "Thing")]:
        r = map_category(*args)
        assert r.status == "needs_review" and r.subcategory_slug is None


def test_whole_words_only():
    assert map_category("Headphones").subcategory_slug == "headphones-speakers"   # not "phones" -> smartphones
    assert map_category("Cricket Bat").subcategory_slug == "football-cricket-equipment"