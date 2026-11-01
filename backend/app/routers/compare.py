import sys
import subprocess
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.db.mongo import get_db
from app.models.external import GroupOut, SearchPage, SourceStatusOut
from app.services import compare_service

router = APIRouter(prefix="/compare", tags=["Compare"])


@router.get("/search", response_model=SearchPage)
def search(
        q: str = Query("", max_length=100),
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        store: Optional[str] = None,
        source: Optional[str] = None, # Added source parameter for FairShare filter
        sort: Literal["price_asc", "price_desc"] = "price_asc",
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=50),
        db=Depends(get_db),
):
    # Pass the source filter to the search service
    result = compare_service.search(db, q, category, subcategory, store, sort, page, page_size, source=source)

    if isinstance(result, dict):
        items_found = result.get("items") or result.get("results") or result.get("products") or []
    else:
        items_found = getattr(result, "items", getattr(result, "results", getattr(result, "products", [])))

    # Only run the live scraper if the user didn't explicitly request "fairshare" only
    if q and page == 1 and len(items_found) < 15 and source != "fairshare":
        print(f"\n--- Low local results ({len(items_found)}) for '{q}'. Triggering live on-demand scrape... ---")

        try:
            subprocess.run(
                [sys.executable, "-m", "app.scrapers.runner", "--query", q],
                check=True,
                timeout=120
            )
            # Re-query after scraping
            result = compare_service.search(db, q, category, subcategory, store, sort, page, page_size, source=source)
            print(f"--- Successfully recovered! Returning newly scraped items for '{q}'. ---\n")

        except subprocess.TimeoutExpired:
            print(f"--- On-demand scrape for '{q}' timed out. ---")
        except Exception as e:
            print(f"--- On-demand scrape failed: {e} ---")

    return result


@router.get("/groups/{group_key}", response_model=GroupOut)
def group(group_key: str, db=Depends(get_db)):
    return compare_service.get_group(db, group_key)


@router.get("/sources", response_model=list[SourceStatusOut])
def sources(db=Depends(get_db)):
    return compare_service.store_sources(db)