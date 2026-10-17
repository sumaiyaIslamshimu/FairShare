
"""Shared enums and helpers used by every module."""
from enum import Enum


class Role(str, Enum):
    user = "user"
    seller = "seller"
    admin = "admin"


class VerificationStatus(str, Enum):
    none = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SellerStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"
