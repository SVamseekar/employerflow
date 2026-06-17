import stripe
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PlanTier, User

settings = get_settings()


def init_stripe():
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key


def plan_from_price_id(price_id: str) -> PlanTier | None:
    if price_id == settings.stripe_price_pro_monthly:
        return PlanTier.pro
    if price_id == settings.stripe_price_premium_monthly:
        return PlanTier.premium
    return None


def create_checkout_session(user: User, plan: PlanTier) -> str:
    init_stripe()
    if not settings.stripe_secret_key:
        raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY in .env")

    price_id = (
        settings.stripe_price_pro_monthly
        if plan == PlanTier.pro
        else settings.stripe_price_premium_monthly
    )
    if not price_id:
        raise ValueError(f"Stripe price ID not configured for {plan.value}")

    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.full_name or user.email)
        user.stripe_customer_id = customer.id

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.app_url}/app.html?billing=success",
        cancel_url=f"{settings.app_url}/app.html?billing=cancel",
        metadata={"user_id": str(user.id), "plan": plan.value},
    )
    return session.url


def create_portal_session(user: User) -> str:
    init_stripe()
    if not user.stripe_customer_id:
        raise ValueError("No billing account found. Subscribe first.")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.app_url}/app.html",
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str, db: Session) -> dict:
    init_stripe()
    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"]["user_id"])
        user = db.get(User, user_id)
        if user and not user.plan_granted:
            plan = PlanTier(session["metadata"].get("plan", "pro"))
            user.plan = plan
            user.stripe_subscription_id = session.get("subscription")
            db.commit()

    elif event["type"] in ("customer.subscription.updated", "customer.subscription.created"):
        sub = event["data"]["object"]
        customer_id = sub["customer"]
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user and not user.plan_granted and sub.get("status") == "active":
            price_id = sub["items"]["data"][0]["price"]["id"]
            plan = plan_from_price_id(price_id)
            if plan:
                user.plan = plan
                user.stripe_subscription_id = sub["id"]
                db.commit()

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        user = db.query(User).filter(User.stripe_customer_id == sub["customer"]).first()
        if user and not user.plan_granted:
            user.plan = PlanTier.free
            user.stripe_subscription_id = None
            db.commit()

    return {"status": "ok"}