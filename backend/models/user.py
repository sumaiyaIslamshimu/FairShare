from datetime import datetime, timezone



    """
    """

    name: str
    email: EmailStr
    hashed_password: str
    role: str = "shopper"
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True
