import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.scrapers.base import BaseScraper, ParseOutcome, RawProduct

class AgoraScraper(BaseScraper):
    store = "agora"  # Changed to lowercase
    base_url = "https://agorasuperstores.com"


    def search_url(self, query: str, page: int = 1) -> str:
        # Agora encodes the search query in Base64
        encoded_query = base64.b64encode(query.encode('utf-8')).decode('utf-8')
        # Appending location=Dhaka as seen in the recon URL
        url = f"{self.base_url}/search?q={encoded_query}&location=Dhaka"
        if page > 1:
            url += f"&page={page}"
        return url

    def parse_listing(self, html: str, page_url: str) -> ParseOutcome:
        soup = BeautifulSoup(html, "lxml")
        products = []
        skipped = 0

        # Agora wraps each product in a div with the 'product-item' class
        cards = soup.find_all("div", class_="product-item")
        
        for card in cards:
            btn = card.find("button", class_="add-to-cart")
            link_tag = card.find("a", href=True)
            
            if not btn or not link_tag:
                skipped += 1
                continue
                
            name = btn.get("data-name")
            price_str = btn.get("data-price")
            image_url = btn.get("data-image")
            prod_id = btn.get("data-prod-id")
            
            if not name or not price_str:
                skipped += 1
                continue
                
            try:
                price = float(price_str)
            except ValueError:
                skipped += 1
                continue
                
            product_url = urljoin(self.base_url, link_tag["href"])
            
            # Out of stock items have disabled="" on the button
            is_disabled = btn.has_attr("disabled")
            availability = "Out of stock" if is_disabled else "In stock"
            
            products.append(RawProduct(
                store=self.store,
                name=name.strip(),
                product_url=product_url,
                price=price,
                currency="BDT",
                image_url=image_url,
                availability=availability,
                store_product_id=prod_id
            ))

        notes = []
        if not products and not skipped:
            notes.append("No product items found on the page.")
            
        return ParseOutcome(products=products, skipped=skipped, notes=notes)