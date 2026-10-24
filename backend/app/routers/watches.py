from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.watch import WatchCreate, WatchHistory, WatchOut, WatchPage, WatchRef, WatchUpdate
from app.services import watch_service

router = APIRouter(prefix="/watches", tags=["Price tracking"])
Shopper = Depends(require_role("user"))


@router.post("", response_model=WatchOut, status_code=201)
def add(body: WatchCreate, user=Shopper, db=Depends(get_db)):
    return watch_service.create(db, user, body)


@router.get("", response_model=WatchPage)
def mine(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), user=Shopper, db=Depends(get_db)):
    return watch_service.list_mine(db, user, page, page_size)


@router.get("/refs", response_model=list[WatchRef])
def my_refs(user=Shopper, db=Depends(get_db)):
    return watch_service.refs(db, user)


@router.get("/{watch_id}/history", response_model=WatchHistory)
def history(watch_id: str, user=Shopper, db=Depends(get_db)):
    return watch_service.history(db, user, watch_id)


@router.patch("/{watch_id}", response_model=WatchOut)
def set_target(watch_id: str, body: WatchUpdate, user=Shopper, db=Depends(get_db)):
    return watch_service.update(db, user, watch_id, body)


@router.delete("/{watch_id}", status_code=204)
def remove(watch_id: str, user=Shopper, db=Depends(get_db)):
    watch_service.delete(db, user, watch_id)
    return Response(status_code=204)