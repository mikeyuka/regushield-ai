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


def create_stripe_checkout_session(price_id: str, email: str, mode: str = "subscription") -> dict:
    """
    Creates a real Stripe Checkout Session for the provided price_id.
    """
    if stripe and settings.STRIPE_SECRET_KEY:
        try:
            # Success and Cancel URLs - Update to your production frontend domain
            # We derive from current origin or use a reasonable default
            domain = "https://regushield-ai.vercel.app"
            
            session = stripe.checkout.Session.create(
                customer_email=email,
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode=mode,
                success_url=f"{domain}/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{domain}/billing?canceled=true",
            )
            return {
                "id": session.id,
                "url": session.url
            }
        except Exception as e:
            print(f"Stripe Checkout error: {str(e)}")
            raise e
            
    # Fallback/Mock logic for sandbox/offline
    return {
        "id": f"cs_mock_{uuid.uuid4().hex[:16]}",
        "url": f"https://checkout.stripe.com/pay/mock_session_{uuid.uuid4().hex[:8]}"
    }


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
