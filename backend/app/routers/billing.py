from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import PlanTier, User
from app.schemas import CheckoutRequest
from app.services import billing

router = APIRouter(prefix="/api/billing", tags=["billing"])
settings = get_settings()


@router.get("/plans")
def list_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "features": [
                    "Browse 100 employers",
                    "Visa filter & search",
                    "Basic dashboard",
                ],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "stripe_configured": bool(settings.stripe_price_pro_monthly),
                "features": [
                    "Full employer directory (15,000+)",
                    "Personalized match scoring",
                    "Top 100 shortlist",
                    "Template-based email drafts",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 49,
                "stripe_configured": bool(settings.stripe_price_premium_monthly),
                "features": [
                    "Everything in Pro",
                    "Top 500 shortlist",
                    "Outreach CRM & Kanban",
                    "Export & priority support",
                ],
            },
        ]
    }


@router.post("/checkout")
def checkout(payload: CheckoutRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = PlanTier.pro if payload.plan == "pro" else PlanTier.premium
    try:
        url = billing.create_checkout_session(user, plan)
        db.commit()
        return {"checkout_url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
def portal(user: User = Depends(get_current_user)):
    try:
        url = billing.create_portal_session(user)
        return {"portal_url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")
    try:
        return billing.handle_webhook(payload, sig, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))