import uuid
from app.config import settings

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
except ImportError:
    stripe = None

try:
    import gocardless_pro
except ImportError:
    gocardless_pro = None


def create_stripe_payment_intent(amount_usd: int, email: str) -> dict:
    """
    Sets up Stripe Intent structure or fallback mock.
    """
    amount_cents = amount_usd * 100
    
    if stripe and settings.STRIPE_SECRET_KEY:
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                receipt_email=email,
                metadata={"email": email}
            )
            return {
                "id": intent.get("id"),
                "client_secret": intent.get("client_secret"),
                "amount": intent.get("amount"),
                "currency": intent.get("currency"),
                "status": intent.get("status"),
                "mode": "live"
            }
        except Exception:
            pass

    mock_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
    mock_client_secret = f"{mock_id}_secret_{uuid.uuid4().hex[:20]}"
    return {
        "id": mock_id,
        "client_secret": mock_client_secret,
        "amount": amount_cents,
        "currency": "usd",
        "status": "requires_payment_method",
        "mode": "mock"
    }


def create_gocardless_billing_request(amount_usd: int, email: str) -> dict:
    """
    Sets up GoCardless Billing Request flow or fallback mock.
    """
    amount_pence = amount_usd * 100
    
    if gocardless_pro and settings.GOCARDLESS_ACCESS_TOKEN:
        try:
            client = gocardless_pro.Client(
                access_token=settings.GOCARDLESS_ACCESS_TOKEN,
                environment="sandbox"
            )
            billing_request = client.billing_requests.create(
                params={
                    "payment_request": {
                        "amount": str(amount_pence),
                        "currency": "USD",
                        "description": "ReguShield Compliance Billing"
                    }
                }
            )
            flow = client.billing_request_flows.create(
                params={
                    "links": {
                        "billing_request": billing_request.id
                    },
                    "prefilled_customer": {
                        "email": email
                    }
                }
            )
            return {
                "billing_request_id": billing_request.id,
                "redirect_url": flow.authorisation_url,
                "mode": "live"
            }
        except Exception:
            pass

    mock_br_id = f"BRQ_{uuid.uuid4().hex[:12].upper()}"
    mock_flow_id = f"BRF_{uuid.uuid4().hex[:12].upper()}"
    mock_redirect_url = f"https://pay.gocardless.com/flow/{mock_flow_id}?email={email}&amount={amount_usd}"
    return {
        "billing_request_id": mock_br_id,
        "redirect_url": mock_redirect_url,
        "mode": "mock"
    }
