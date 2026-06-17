# EmployerFlow

Production-ready SaaS for visa-aware employer discovery. No LLM at any stage — deterministic scoring, template-based outreach, Stripe subscriptions.

**Infrastructure cost: $0/month** — see [FREE_STACK.md](FREE_STACK.md)

**Stack:** FastAPI · PostgreSQL (Neon free) · Render free · Stripe (pay-per-sale only)

---

## Deploy free (production)

1. Create free DB at [neon.tech](https://neon.tech) → copy connection string
2. Deploy at [Render Blueprint](https://dashboard.render.com/select-repo?repo=https://github.com/SVamseekar/employerflow) → paste `DATABASE_URL`
3. Delete Railway project if you created one earlier (not free)

Full guide: **[FREE_STACK.md](FREE_STACK.md)**

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

## Deploy to production (free)

See **[FREE_STACK.md](FREE_STACK.md)** — Render Free + Neon Free Postgres. No credit card required.

Paid alternatives (Fly.io, Railway, Render Starter) are documented in `DEPLOYMENT.md` but not needed.

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