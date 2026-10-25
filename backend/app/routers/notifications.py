from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.notification import MarkedRead, NotificationOut, NotificationPage, UnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationPage)
def my_notifications(unread_only: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50),
                     user=Depends(get_current_user), db=Depends(get_db)):
    return notification_service.list_mine(db, user, unread_only, page, page_size)


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(user=Depends(get_current_user), db=Depends(get_db)):
    return {"unread": notification_service.unread_count(db, user)}


@router.post("/read-all", response_model=MarkedRead)
def read_all(user=Depends(get_current_user), db=Depends(get_db)):
    return {"marked": notification_service.mark_all_read(db, user)}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_one(notification_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return notification_service.mark_read(db, user, notification_id)