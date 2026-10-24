"""Verification contracts. Raw NID data is never part of any schema in this file."""
from typing import Optional

from pydantic import BaseModel

from app.models.common import VerificationStatus


class VerificationStatusOut(BaseModel):
    """What the account owner may see: status only (plus the admin's note when rejected)."""
    status: VerificationStatus
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    note: Optional[str] = None
    manual_review: bool = True  # verification is reviewed by a person, not an automatic service