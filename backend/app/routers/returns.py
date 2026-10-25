from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.returns import ReturnCreate, ReturnDecision, ReturnOut, ReturnPage, ReturnStaffOut, ReturnStaffPage
from app.services import return_service

router = APIRouter(tags=["Returns"])
PageQ = Query(1, ge=1)
SizeQ = Query(20, ge=1, le=50)
Status = Optional[Literal["requested", "approved", "rejected", "completed", "cancelled"]]


@router.post("/returns", response_model=ReturnOut, status_code=201)
def request_return(body: ReturnCreate, user=Depends(require_role("user")), db=Depends(get_db)):
    return return_service.create(db, user, body)


@router.get("/returns/mine", response_model=ReturnPage)
def my_returns(page: int = PageQ, page_size: int = SizeQ, user=Depends(require_role("user")), db=Depends(get_db)):
    return return_service.list_mine(db, user, page, page_size)


@router.post("/returns/{return_id}/cancel", response_model=ReturnOut)
def cancel_return(return_id: str, user=Depends(require_role("user")), db=Depends(get_db)):
    return return_service.cancel(db, user, return_id)


@router.get("/seller/returns", response_model=ReturnStaffPage)
def seller_returns(status: Status = None, page: int = PageQ, page_size: int = SizeQ,
                   seller=Depends(require_role("seller")), db=Depends(get_db)):
    return return_service.list_for_seller(db, seller, status, page, page_size)


@router.patch("/seller/returns/{return_id}", response_model=ReturnStaffOut)
def seller_decide(return_id: str, body: ReturnDecision, seller=Depends(require_role("seller")), db=Depends(get_db)):
    return return_service.decide_as_seller(db, seller, return_id, body)