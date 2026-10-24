from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.complaint import ComplaintCreate, ComplaintOut, ComplaintPage
from app.services import complaint_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
def file_complaint(body: ComplaintCreate, user=Depends(require_role("user", "seller")), db=Depends(get_db)):
    return complaint_service.file_complaint(db, user, body)


@router.get("", response_model=ComplaintPage)
def my_complaints(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  user=Depends(require_role("user", "seller")), db=Depends(get_db)):
    return complaint_service.list_mine(db, user, page, page_size)