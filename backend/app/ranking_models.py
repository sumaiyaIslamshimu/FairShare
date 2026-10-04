from typing import Optional, List, Dict

from pydantic import BaseModel

from app.models import ProductHeader


class ListingScoreOut(BaseModel):
    id: str
    marketplace: str
    seller: Optional[str] = None
    price: float
    delivery_cost: Optional[float] = None
    rating: float
    discount: Optional[float] = None
    product_url: Optional[str] = None
    score: float
    score_breakdown: Dict[str, float]


class ProductRankingResponse(BaseModel):
    product: ProductHeader
    listings: List[ListingScoreOut]