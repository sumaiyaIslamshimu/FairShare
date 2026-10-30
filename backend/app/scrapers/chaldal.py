"""Chaldal adapter utilizing the internal mobile/web API to bypass CAPTCHA.

STATUS: CONFIGURED via direct API interaction.
"""
from typing import Optional
import httpx

from app.scrapers.base import BaseScraper, ScrapeResult, ScrapeStatus, RawProduct, Fetcher, RobotsChecker


class ChaldalScraper(BaseScraper):
    store = "chaldal"
    base_url = "https://chaldal.com"
    api_url = "https://catalog.chaldal.com/searchPersonalized"

    def search_url(self, query: str, page: int = 1) -> str:
        # We still need a valid web URL for the frontend to link users to the search page
        from urllib.parse import quote_plus
        return f"{self.base_url}/search/{quote_plus(query)}"

    def parse_listing(self, html: str, page_url: str):
        # We bypass HTML parsing entirely by overriding the run() method below
        pass

    def run(self, query: str, fetcher: Fetcher, robots: Optional[RobotsChecker] = None,
            limit: int = 20, page: int = 1) -> ScrapeResult:

        web_url = self.search_url(query, page)
        result = ScrapeResult(store=self.store, status=ScrapeStatus.failure, url=web_url)

        # 1. Check robots.txt (Chaldal does not block via robots.txt, but we play by the rules)
        if robots is not None:
            allowed = robots.allowed(web_url)
            result.robots_allowed = allowed
            if not allowed:
                result.status = ScrapeStatus.unsupported
                result.notes.append("robots.txt disallows automated access.")
                return result

        # 2. Format the hidden API request using the intercepted payload
        payload = {
            "apiKey": "e964fc2d51064efa97e94db7c64bf3d044279d4ed0ad4bdd9dce89fecc9156f0",
            "storeId": 1,
            "warehouseId": 8,
            "pageSize": limit,
            "currentPageIndex": page - 1,
            "metropolitanAreaId": 1,
            "query": query,
            "productVariantId": -1,
            "canSeeOutOfStock": "true",
            "filters": []
        }

        headers = {
            "User-Agent": "FairShareBot/0.1 (university project; price comparison)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/"
        }

        # 3. Fetch directly from the API, bypassing the HTML fetcher and Cloudflare entirely
        try:
            r = httpx.post(self.api_url, json=payload, headers=headers, timeout=15.0)
            result.http_status = r.status_code
            r.raise_for_status()

            data = r.json()
            hits = data.get("hits", [])

            # 4. Parse the pristine JSON objects into RawProducts
            for hit in hits:
                pics = hit.get("picturesUrls", [])
                image_url = pics[0] if pics else None

                # Evaluate stock level from the warehouse array
                stock_data = hit.get("productAvailabilityForSelectedWarehouse", [])
                in_stock = any(wh.get("Quantity", 0) > 0 for wh in stock_data)
                availability = "In Stock" if in_stock else "Out of Stock"

                product = RawProduct(
                    store=self.store,
                    name=hit.get("name"),
                    product_url=f"{self.base_url}/p/{hit.get('slug')}",
                    price=hit.get("price"),
                    currency="৳",
                    image_url=image_url,
                    availability=availability,
                    store_product_id=str(hit.get("objectID"))
                )
                result.products.append(product)

            result.status = ScrapeStatus.success
            if not result.products:
                result.notes.append("valid empty result: the API returned no products.")

        except httpx.TimeoutException:
            result.errors.append("API Request timed out.")
        except httpx.HTTPStatusError as e:
            result.errors.append(f"API HTTP Error: {e.response.status_code}")
        except Exception as e:
            result.errors.append(f"API Parse Error: {type(e).__name__} - {str(e)}")

        return result