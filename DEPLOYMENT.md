# EmployerFlow — Deployment Status

**Last deployed:** 2026-06-17

## Production (Railway) — LIVE

| Resource | URL |
|----------|-----|
| **App** | https://employerflow-api-production.up.railway.app |
| **Landing** | https://employerflow-api-production.up.railway.app/ |
| **Dashboard** | https://employerflow-api-production.up.railway.app/app.html |
| **API Health** | https://employerflow-api-production.up.railway.app/api/health |
| **GitHub** | https://github.com/SVamseekar/employerflow |
| **Railway Dashboard** | https://railway.com/project/7bb7f581-02b0-4370-a933-d07c34117cbc |

**Database:** Railway Postgres (auto-seeded with 14,674 employers on first boot)

## Local (Docker Compose)

```bash
make up    # http://localhost:8000
```

## Stripe (payments — not yet configured)

1. Run `bash scripts/setup_stripe.sh`
2. Add keys to Railway: `railway variables --set STRIPE_SECRET_KEY=sk_...` etc.
3. Webhook URL: `https://employerflow-api-production.up.railway.app/api/billing/webhook`

## Fly.io (blocked — needs billing)

Fly login works (`martisoura@gmail.com`) but app creation requires a credit card:
https://fly.io/dashboard/marti-soura-vamseekar/billing

`fly.toml` is ready — deploy after adding payment method:

```bash
fly apps create employerflow
fly postgres create --name employerflow-db --region fra
fly postgres attach employerflow-db -a employerflow
fly secrets set SECRET_KEY=... APP_URL=https://employerflow.fly.dev -a employerflow
fly deploy
```

## Render (alternative)

Connect GitHub repo at https://dashboard.render.com/select-repo?repo=https://github.com/SVamseekar/employerflow

Blueprint file: `render.yaml`