import pytest
from pathlib import Path
from app.scrapers.agora import AgoraScraper


def test_agora_parser():
    # Load the fixture saved from the recon tool
    fixture_path = Path(__file__).resolve().parents[0] / "fixtures" / "agora" / "recon_page.html"
    html = fixture_path.read_text(encoding="utf-8")

    scraper = AgoraScraper()
    outcome = scraper.parse_listing(html, "https://agorasuperstores.com/search?q=cmljZQ==&location=Dhaka")

    assert len(outcome.products) > 0
    assert outcome.skipped == 0

    # Check the first product (Green Field standard miniket rice)
    p1 = outcome.products[0]
    assert p1.store == "Agora"
    assert "Green Field" in p1.name
    assert p1.price == 60.0
    assert p1.currency == "BDT"
    assert "agorasuperstores.com/product-details" in p1.product_url
    assert p1.store_product_id == "11933"
    assert p1.availability == "In stock"

    # Check an out of stock product (e.g. Green Field kataribogh)
    out_of_stock_item = next((p for p in outcome.products if p.store_product_id == "13908"), None)
    assert out_of_stock_item is not None
    assert out_of_stock_item.availability == "Out of stock"