import os
import stripe
import sys

# Sandbox Secret Key should be set via STRIPE_SECRET_KEY environment variable
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")

def create_products():
    if not STRIPE_SECRET_KEY:
        print("Error: STRIPE_SECRET_KEY environment variable not set.")
        sys.exit(1)

    stripe.api_key = STRIPE_SECRET_KEY

    plans = [
        {
            "name": "Starter Plan",
            "price": 199,
            "interval": None, # One-time
            "description": "Single UK REACH threshold validation and OCR extraction."
        },
        {
            "name": "Professional Tier",
            "price": 199,
            "interval": "month",
            "description": "Continuous monitoring and automated compliance drift alerts."
        },
        {
            "name": "Growth Acceleration",
            "price": 499,
            "interval": "month",
            "description": "Unlimited validation and multi-market (UK/EU/US) support."
        },
        {
            "name": "Enterprise Solutions",
            "price": 1499,
            "interval": "month",
            "description": "Full-scale automation with custom API integration and expert review."
        }
    ]

    results = []

    print(f"Initializing Stripe product creation (Sandbox Mode)...")
    
    for plan in plans:
        try:
            # Create Product
            product = stripe.Product.create(
                name=plan["name"],
                description=plan["description"],
            )

            # Create Price
            price_data = {
                "unit_amount": plan["price"] * 100,
                "currency": "usd",
                "product": product.id,
            }

            if plan["interval"]:
                price_data["recurring"] = {"interval": plan["interval"]}

            price = stripe.Price.create(**price_data)

            results.append({
                "name": plan["name"],
                "product_id": product.id,
                "price_id": price.id,
                "amount": f"${plan['price']}",
                "type": "Recurring" if plan["interval"] else "One-time"
            })
            print(f"Created {plan['name']} ({price.id})")

        except Exception as e:
            print(f"Failed to create {plan['name']}: {str(e)}")

    print("\n" + "="*50)
    print("REGUSHIELD STRIPE PRICE IDs (USD)")
    print("="*50)
    for res in results:
        print(f"{res['name']} [{res['type']}]: {res['price_id']}")
    print("="*50)

    # Save to a text file for easy copy-pasting
    with open("stripe_price_ids.txt", "w") as f:
        f.write("REGUSHIELD STRIPE PRICE IDs\n")
        for res in results:
            f.write(f"{res['name']}: {res['price_id']}\n")
    
    print("\nResults saved to [stripe_price_ids.txt](stripe_price_ids.txt)")

if __name__ == "__main__":
    create_products()
