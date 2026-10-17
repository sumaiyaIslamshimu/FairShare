from pydantic import BaseModel


class SubcategoryOut(BaseModel):
    slug: str
    name: str


class CategoryOut(BaseModel):
    slug: str
    name: str
    subcategories: list[SubcategoryOut]