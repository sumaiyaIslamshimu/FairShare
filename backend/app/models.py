from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

# This safely converts MongoDB ObjectIds to strings for Pydantic V2
PyObjectId = Annotated[str, BeforeValidator(str)]

class Product(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    brand: str
    category: str
    price: float
    rating: float
    image_link: Optional[str] = None
    marketplace_name: str
    product_link: Optional[str] = None
    in_stock: bool = True
    is_verified: bool = False

    model_config = ConfigDict(populate_by_name=True)