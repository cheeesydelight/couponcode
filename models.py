from typing import Optional, List
from pydantic import BaseModel

class CouponCreate(BaseModel):
    code: str
    type: str  # must be "percent"
    amount: float
    uses: Optional[int] = -1
    expiresAt: Optional[str] = None

class CouponResponse(BaseModel):
    message: str

class CartItem(BaseModel):
    id: str
    name: str
    price: float
    qty: int

class CouponValidateRequest(BaseModel):
    sessionId: str
    code: str
    cart: List[CartItem]

class CouponValidateResponse(BaseModel):
    valid: bool
    discount: Optional[float] = 0
    newTotal: Optional[float] = 0
    message: str
