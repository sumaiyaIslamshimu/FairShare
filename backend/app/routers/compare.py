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
    sort: Literal["price_asc", "price_desc"] = "price_asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db=Depends(get_db),
):
    return compare_service.search(db, q, category, subcategory, store, sort, page, page_size)


@router.get("/groups/{group_key}", response_model=GroupOut)
def group(group_key: str, db=Depends(get_db)):
    return compare_service.get_group(db, group_key)


@router.get("/sources", response_model=list[SourceStatusOut])
def sources(db=Depends(get_db)):
    return compare_service.store_sources(db)