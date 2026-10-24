from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.verification import VerificationStatusOut
from app.services import verification_service

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/submit", response_model=VerificationStatusOut, status_code=201)
def submit(nid_number: str = Form(..., max_length=40), document: UploadFile = File(...),
           user=Depends(require_role("user", "seller")), db=Depends(get_db)):
    """Multipart form: NID number + one PDF/JPG/PNG document (max 5 MB). Returns the status only."""
    return verification_service.submit(db, user, nid_number, document)


@router.get("/status", response_model=VerificationStatusOut)
def status(user=Depends(require_role("user", "seller")), db=Depends(get_db)):
    return verification_service.status_for(db, user)