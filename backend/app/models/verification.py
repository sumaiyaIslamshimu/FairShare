"""Verification contracts. Raw NID data is never part of any public schema."""
from pydantic import BaseModel

from app.models.common import VerificationStatus


class VerificationStatusOut(BaseModel):
    status: VerificationStatus