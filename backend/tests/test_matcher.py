from app.scrapers.matcher import exact_group_key, match_products


def p(name, brand=None, q=None, u=None, sub=None):
    return {"name": name, "brand": brand, "quantity": q, "unit": u, "subcategory_slug": sub}


def test_identical_product_across_stores_is_exact():
    a = p("Pran Miniket Rice 5 kg", "Pran", 5000.0, "g")
    b = p("Miniket Rice 5kg Pran", "PRAN", 5000.0, "g")
    r = match_products(a, b)
    assert r.match_type == "exact" and not r.differences
    assert exact_group_key(a) == exact_group_key(b) and exact_group_key(a) is not None


def test_different_package_size_is_possible_never_exact():
    r = match_products(p("Pran Miniket Rice 5 kg", "Pran", 5000.0, "g"), p("Pran Miniket Rice 1 kg", "Pran", 1000.0, "g"))
    assert r.match_type == "possible"
    assert {"field": "package_size", "a": "5000 g", "b": "1000 g"} in r.differences
    assert exact_group_key(p("Pran Miniket Rice 5 kg", "Pran", 5000.0, "g")) != exact_group_key(
        p("Pran Miniket Rice 1 kg", "Pran", 1000.0, "g"))


def test_different_model_variant_is_not_exact():
    r = match_products(p("Samsung Galaxy A54 128GB", "Samsung"), p("Samsung Galaxy A54 256GB", "Samsung"))
    assert r.match_type == "possible"
    assert any(d["field"] == "model_or_variant" for d in r.differences)
    r2 = match_products(p("Apple iPhone 15 Pro", "Apple"), p("Apple iPhone 16 Pro", "Apple"))
    assert r2.match_type == "possible" and any(d["field"] == "model_or_variant" for d in r2.differences)


def test_different_brands_never_match():
    assert match_products(p("Rice 1 kg", "Pran", 1000.0, "g"), p("Rice 1 kg", "Teer", 1000.0, "g")).match_type == "none"


def test_similar_names_alone_are_not_exact_when_brand_missing():
    r = match_products(p("Wireless Bluetooth Headphones Black"), p("Wireless Bluetooth Headphones Black"))
    assert r.match_type == "possible" and any(d["field"] == "brand" for d in r.differences)
    assert exact_group_key(p("Wireless Bluetooth Headphones Black")) is None


def test_incomparable_units_and_categories_are_none():
    assert match_products(p("Soy Oil 1 L", "Teer", 1000.0, "ml"), p("Soy Oil 1 kg", "Teer", 1000.0, "g")).match_type == "none"
    assert match_products(p("Teer Product X", "Teer", sub="home-appliances"), p("Teer Product X", "Teer", sub="beverages")).match_type == "none"


def test_unrelated_products_are_none():
    assert match_products(p("Sony WH-1000XM5 Headphones", "Sony"), p("Sony Bravia 55 Inch TV", "Sony")).match_type == "none"


def test_size_stated_on_one_side_only_is_possible():
    r = match_products(p("Pran Miniket Rice", "Pran"), p("Pran Miniket Rice 5 kg", "Pran", 5000.0, "g"))
    assert r.match_type == "possible" and any(d["field"] == "package_size" for d in r.differences)