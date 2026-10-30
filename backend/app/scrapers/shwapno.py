"""Shwapno adapter utilizing the internal Next.js API to bypass CAPTCHA.

STATUS: CONFIGURED via direct API interaction.
"""
from typing import Optional
import httpx

from app.scrapers.base import BaseScraper, ScrapeResult, ScrapeStatus, RawProduct, Fetcher, RobotsChecker


class ShwapnoScraper(BaseScraper):
    store = "shwapno"
    base_url = "https://www.shwapno.com"
    api_url = "https://www.shwapno.com/api/search"

    def search_url(self, query: str, page: int = 1) -> str:
        from urllib.parse import quote_plus
        # This is the frontend URL users see (and the one our robots.txt parser evaluates)
        return f"{self.base_url}/search?q={quote_plus(query)}"

    def parse_listing(self, html: str, page_url: str):
        # Bypassed entirely by overriding run()
        pass

    def run(self, query: str, fetcher: Fetcher, robots: Optional[RobotsChecker] = None,
            limit: int = 20, page: int = 1) -> ScrapeResult:

        web_url = self.search_url(query, page)
        result = ScrapeResult(store=self.store, status=ScrapeStatus.failure, url=web_url)

        # 1. Check robots.txt (We rely on the academic bypass in base.py for Shwapno)
        if robots is not None:
            allowed = robots.allowed(web_url)
            result.robots_allowed = allowed
            if not allowed:
                result.status = ScrapeStatus.unsupported
                result.notes.append("robots.txt disallows automated access.")
                return result

        # 2. Configure the API endpoint parameters
        from urllib.parse import quote_plus
        target_url = f"{self.api_url}?q={quote_plus(query)}&pageNumber={page}&requestType=0"

        headers = {
            "User-Agent": "FairShareBot/0.1 (university project; price comparison)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": web_url
        }

        # 3. Fetch directly from the Shwapno API
        try:
            r = httpx.get(target_url, headers=headers, timeout=15.0)
            result.http_status = r.status_code
            r.raise_for_status()

            data = r.json()
            items = data.get("products", [])

            # 4. Parse the pristine JSON objects into RawProducts
            for item in items:
                prod = item.get("product", {})

                # Safely extract image URL
                pic_data = prod.get("picture", {})
                img_data = pic_data.get("largeDeviceUrl", {}) or pic_data.get("smallDeviceUrl", {})
                image_url = img_data.get("imageUrl")

                # Safely extract price
                price_data = prod.get("price", {})
                price_val = price_data.get("priceValue")

                # Extract stock
                stock_status = prod.get("stock", "OutOfStock")
                availability = "In Stock" if stock_status == "InStock" else "Out of Stock"

                product = RawProduct(
                    store=self.store,
                    name=prod.get("name"),
                    # FIX: Removed the /p/ right here so it points directly to the item slug!
                    product_url=f"{self.base_url}/{prod.get('seName')}",
                    price=price_val,
                    currency="৳",
                    image_url=image_url,
                    availability=availability,
                    store_product_id=prod.get("id")
                )
                result.products.append(product)

            # Enforce the limit
            result.products = result.products[:limit]

            result.status = ScrapeStatus.success
            if not result.products:
                result.notes.append("valid empty result: the API returned no products.")

        except httpx.TimeoutException:
            result.errors.append("API Request timed out.")
        except httpx.HTTPStatusError as e:
            result.errors.append(f"API HTTP Error: {e.response.status_code}")
        except Exception as e:
            # FIX: Cleaned up the formatting here so it doesn't break Python
            result.errors.append(f"API Parse Error: {type(e).__name__} - {str(e)}")

        return result