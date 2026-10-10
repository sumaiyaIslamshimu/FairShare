from datetime import date
from typing import Literal

from pydantic import BaseModel, model_validator


class RentalRequestCreate(BaseModel):
    product_id: str
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date < date.today():
            raise ValueError("Rental start date cannot be in the past.")

        if self.end_date < self.start_date:
            raise ValueError(
                "End date must be on or after the start date."
            )

        return self


class RentalStatusUpdate(BaseModel):
    status: Literal["accepted", "declined"]