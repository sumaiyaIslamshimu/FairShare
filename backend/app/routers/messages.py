"""FastAPI endpoints for Unified Messaging."""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.message import MessageCreateIn, MessageOut, ThreadSummaryOut
from app.services import message_service

router = APIRouter(prefix="/messages", tags=["Messaging"])


@router.post("", response_model=MessageOut, status_code=201)
def send_message(body: MessageCreateIn, user=Depends(get_current_user), db=Depends(get_db)):
    return message_service.send_message(db, user, body)


@router.get("/threads", response_model=list[ThreadSummaryOut])
def list_threads(user=Depends(get_current_user), db=Depends(get_db)):
    return message_service.get_threads(db, user)


@router.get("/threads/{thread_id}", response_model=list[MessageOut])
def get_thread_messages(thread_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return message_service.get_messages(db, user, thread_id)