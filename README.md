# EmployerFlow

Production-ready SaaS for visa-aware employer discovery. No LLM at any stage — deterministic scoring, template-based outreach, Stripe subscriptions.

**Live stack:** FastAPI · PostgreSQL · Stripe · JWT auth · Docker

---

## Quick start (local)

```bash
cd /Users/souravamseekarmarti/Projects/employerflow
cp .env.example .env
# Edit SECRET_KEY: openssl rand -hex 32

make up          # starts Postgres + API on :8000
make import      # loads 15k employers from employer-discovery CSV
make health      # verify API is up
```

Open **http://localhost:8000** (landing) · **http://localhost:8000/app.html** (app)

---

## Plans

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | Browse 100 employers, visa filters |
| Pro | $29/mo | Full directory, scoring, top 100 shortlist, email drafts |
| Premium | $49/mo | Top 500 shortlist, CRM, export |

---

## Stripe setup (required for payments)

```bash
bash scripts/setup_stripe.sh
```

1. Create two Stripe products (Pro $29, Premium $49)
2. Add price IDs and secret key to `.env`
3. Create webhook → `https://yourdomain.com/api/billing/webhook`
4. Local testing: `stripe listen --forward-to localhost:8000/api/billing/webhook`

---

## Deploy to production

### Option A — Fly.io

```bash
# Install flyctl, then:
fly postgres create --name employerflow-db
fly postgres attach employerflow-db

fly secrets set \
  SECRET_KEY=$(openssl rand -hex 32) \
  STRIPE_SECRET_KEY=sk_live_... \
  STRIPE_WEBHOOK_SECRET=whsec_... \
  STRIPE_PRICE_PRO_MONTHLY=price_... \
  STRIPE_PRICE_PREMIUM_MONTHLY=price_... \
  APP_URL=https://employerflow.fly.dev

cd deploy && fly deploy
```

Import employers after first deploy:

```bash
fly ssh console -C "python /app/scripts/import_employers.py"
```

### Option B — Railway / Render

1. Add PostgreSQL plugin
2. Set env vars from `.env.example`
3. Deploy from `backend/Dockerfile`
4. Mount or bake `frontend/static` into image
5. Run `scripts/import_employers.py` once

### Option C — VPS (Docker Compose)

```bash
# On server:
git clone <repo> && cd employerflow
cp .env.example .env  # set APP_URL to your domain, production secrets
docker compose up -d --build
make import
```

Put Caddy or Nginx in front for HTTPS:

```
yourdomain.com {
  reverse_proxy localhost:8000
}
```

---

## Project structure

```
employerflow/
├── backend/app/          # FastAPI application
│   ├── routers/          # auth, billing, employers, shortlist, CRM
│   └── services/         # scoring, email templates, Stripe
├── frontend/static/      # Landing + app UI
├── scripts/              # Data import, Stripe setup helper
├── deploy/               # Fly.io config
└── docker-compose.yml
```

---

## API overview

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/auth/register` | — | Create account |
| `POST /api/auth/login` | — | Get JWT |
| `GET /api/employers` | JWT | Paginated directory |
| `POST /api/shortlist/generate` | Pro+ | Score & shortlist |
| `POST /api/billing/checkout` | JWT | Stripe Checkout URL |
| `POST /api/billing/webhook` | Stripe sig | Subscription events |

---

## Environment variables

See `.env.example` for full list. Required for production:

- `SECRET_KEY` — JWT signing (32+ random bytes)
- `DATABASE_URL` — PostgreSQL connection string
- `APP_URL` — public URL (for Stripe redirects)
- `STRIPE_*` — payment processing

---

## License

Proprietary. All rights reserved.