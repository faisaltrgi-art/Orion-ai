"""Payment endpoints."""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import get_current_user
from app.db import get_db
from app.db.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = settings.stripe_secret


class PlanResponse(BaseModel):
    id: str
    name: str
    credits: int
    price: float
    features: list


class CheckoutResponse(BaseModel):
    url: str


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return [
        PlanResponse(id="free", name="Free", credits=3, price=0, features=["2 وكلاء", "3 طلبات/يوم"]),
        PlanResponse(id="pro", name="Pro", credits=10, price=9.99, features=["4 وكلاء", "10 طلبات/يوم", "تحليل متقدم"]),
        PlanResponse(id="business", name="Business", credits=50, price=29.99, features=["جميع الوكلاء", "50 طلب/يوم", "أولوية المعالجة", "دعم فني"]),
    ]


@router.post("/checkout/{plan}", response_model=CheckoutResponse)
async def create_checkout(plan: str, current_user: dict = Depends(get_current_user)):
    prices = {"pro": settings.stripe_price_pro, "business": settings.stripe_price_business}
    if plan not in prices:
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": prices[plan], "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/payment/cancel",
            metadata={"user_id": str(current_user["sub"]), "plan": plan},
            client_reference_id=str(current_user["sub"]),
        )
        return CheckoutResponse(url=session.url)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session.get("metadata", {}).get("user_id", 0))
        plan = session.get("metadata", {}).get("plan", "free")

        if user_id:
            async with get_db() as db:
                from datetime import date, timedelta
                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.plan = plan
                    user.plan_expiry = date.today() + timedelta(days=30)
                    user.credits = settings.plans[plan]["credits"]
                    await db.commit()

    return {"status": "ok"}
