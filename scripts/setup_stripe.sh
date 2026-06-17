#!/usr/bin/env bash
# Run after creating Stripe products. Prints env vars to add to .env
set -euo pipefail

echo "=== EmployerFlow Stripe Setup ==="
echo ""
echo "1. Go to https://dashboard.stripe.com/products"
echo "2. Create product 'EmployerFlow Pro' with recurring price \$29/month"
echo "3. Create product 'EmployerFlow Premium' with recurring price \$49/month"
echo "4. Copy the price IDs (price_...) into .env:"
echo ""
echo "   STRIPE_PRICE_PRO_MONTHLY=price_..."
echo "   STRIPE_PRICE_PREMIUM_MONTHLY=price_..."
echo ""
echo "5. Get API keys from https://dashboard.stripe.com/apikeys"
echo "   STRIPE_SECRET_KEY=sk_live_... (or sk_test_ for testing)"
echo ""
echo "6. Create webhook endpoint: ${APP_URL:-http://localhost:8000}/api/billing/webhook"
echo "   Events: checkout.session.completed, customer.subscription.*"
echo "   STRIPE_WEBHOOK_SECRET=whsec_..."
echo ""
echo "7. For local webhook testing:"
echo "   stripe listen --forward-to localhost:8000/api/billing/webhook"