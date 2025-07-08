from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Header, HTTPException, Request
from models import (
    CouponCreate, CouponResponse,
    CouponValidateRequest, CouponValidateResponse, CartItem
)
from firebase_util import db_ref
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# 🔐 Allow frontend CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_KEY = os.getenv("ADMIN_API_KEY")

# 🔐 Admin API key check
def check_admin(api_key: str = Header(..., alias="x-api-key")):
    if api_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# 🎯 1. CREATE COUPON
@app.post("/api/coupons", response_model=CouponResponse)
def create_coupon(coupon: CouponCreate, api_key: str = Header(..., alias="x-api-key")):
    check_admin(api_key)

    # ✅ Enforce only 'percent'
    if coupon.type != "percent":
        raise HTTPException(status_code=400, detail="Only 'percent' type coupons are allowed")

    coupon_ref = db_ref.child("coupons").child(coupon.code.upper())
    if coupon_ref.get():
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    data = {
        "type": coupon.type,
        "amount": coupon.amount,
        "usesLeft": coupon.uses if coupon.uses is not None else -1
    }

    if coupon.expiresAt:
        data["expiresAt"] = coupon.expiresAt

    coupon_ref.set(data)
    return {"message": f"✅ Coupon {coupon.code.upper()} created successfully"}


# 🎯 2. VALIDATE COUPON
@app.post("/api/coupons/validate", response_model=CouponValidateResponse)
def validate_coupon(body: CouponValidateRequest, request: Request):
    session_id = body.sessionId
    code = body.code.strip().upper()

    # Check if already used
    used = db_ref.child("couponUsage").child(session_id).get()
    if used and used.get("coupon") == code:
        return {
            "valid": False,
            "message": "❌ Coupon already used in this session"
        }

    # Load coupon
    data = db_ref.child("coupons").child(code).get()
    if not data:
        return {
            "valid": False,
            "message": "❌ Invalid coupon"
        }

    if data["usesLeft"] != -1 and data["usesLeft"] <= 0:
        return {
            "valid": False,
            "message": "❌ Coupon usage limit reached"
        }

    if "expiresAt" in data:
        try:
            if datetime.utcnow() > datetime.fromisoformat(data["expiresAt"].replace("Z", "")):
                return {
                    "valid": False,
                    "message": "❌ Coupon has expired"
                }
        except:
            pass

    # Merge previous items from order (if any)
    prev = db_ref.child("orders").child(session_id).get()
    previous_items = prev.get("items", []) if prev else []
    current_items = [i.dict() for i in body.cart]
    all_items = previous_items + current_items

    # Merge identical items
    merged = {}
    for item in all_items:
        item_id = item["id"]
        if item_id not in merged:
            merged[item_id] = item.copy()
        else:
            merged[item_id]["qty"] += item["qty"]

    items = list(merged.values())
    subtotal = sum(i["price"] * i["qty"] for i in items)

    # ✅ Only percent coupons now
    if data["type"] != "percent":
        return {
            "valid": False,
            "message": "❌ Only percentage-based coupons are supported"
        }

    discount = round(subtotal * (data["amount"] / 100))
    discount = min(discount, subtotal)
    new_total = subtotal - discount

    label = f"{data['amount']}% off"

    return {
        "valid": True,
        "discount": discount,
        "newTotal": new_total,
        "message": f"✅ {code} applied – {label}"
    }


# 🎯 3. REDEEM COUPON
@app.post("/api/coupons/{code}/redeem")
def redeem_coupon(code: str, sessionId: str):
    code = code.strip().upper()

    used = db_ref.child("couponUsage").child(sessionId).get()
    if used and used.get("coupon") == code:
        return {"success": False, "message": "❌ Already redeemed"}

    coupon_ref = db_ref.child("coupons").child(code)
    data = coupon_ref.get()
    if not data:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if data["usesLeft"] != -1:
        new_uses = max(0, data["usesLeft"] - 1)
        coupon_ref.child("usesLeft").set(new_uses)

    db_ref.child("couponUsage").child(sessionId).set({
        "coupon": code,
        "usedAt": datetime.utcnow().isoformat()
    })

    return {"success": True, "message": f"✅ Coupon {code} redeemed"}
