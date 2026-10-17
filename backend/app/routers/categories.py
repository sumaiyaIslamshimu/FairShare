from fastapi import APIRouter, Depends

from app.db.mongo import get_db
from app.models.category import CategoryOut
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db=Depends(get_db)):
    return category_service.list_tree(db)