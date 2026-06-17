# EmployerFlow — 100% Free Infrastructure

Everything below costs **$0/month**. No credit card required on any tier (except Stripe, which only charges per sale).

## Free stack architecture

```
┌─────────────────────┐     ┌──────────────────────┐
│  Render Free Web    │────▶│  Neon Free Postgres  │
│  (Docker / FastAPI) │     │  (persistent DB)     │
└─────────────────────┘     └──────────────────────┘
         │
         ▼
┌─────────────────────┐
│  GitHub (free repo) │
└─────────────────────┘
```

| Component | Provider | Cost | Limits |
|-----------|----------|------|--------|
| API + UI | [Render Free](https://render.com/docs/free) | $0 | Spins down after 15 min idle; ~1 min cold start |
| Database | [Neon Free](https://neon.tech/pricing) | $0 | 0.5 GB storage; scales to zero when idle |
| Source code | GitHub | $0 | Private repo included |
| Local dev | Docker Compose | $0 | Runs on your machine |
| Payments | Stripe | $0/month | 2.9% + 30¢ per successful charge only |
| LLM / AI APIs | None | $0 | Not used |

**Do NOT use:** Railway (paid after trial), Render Starter Postgres (paid), Fly.io (requires card).

---

## Step 1 — Tear down Railway (stop future charges)

If you deployed to Railway earlier:

1. Open https://railway.com/project/7bb7f581-02b0-4370-a933-d07c34117cbc
2. **Settings → Danger → Delete Project**

---

## Step 2 — Create free Neon database (5 min)

1. Sign up at https://neon.tech (free, no card)
2. Create project: `employerflow`
3. Copy the **connection string** (looks like `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`)
4. Keep it — you'll paste it into Render in Step 3

---

## Step 3 — Deploy to Render Free (10 min)

1. Sign up at https://render.com (Hobby workspace = free)
2. **New → Blueprint** → connect repo: `https://github.com/SVamseekar/employerflow`
3. Render reads `render.yaml` automatically (plan: **free**)
4. Set these env vars when prompted:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Neon connection string |
| `APP_URL` | `https://employerflow-api.onrender.com` (or your Render URL) |
| `CORS_ORIGINS` | Same as `APP_URL` |

5. Deploy. First boot auto-seeds ~14,600 employers (takes 1–2 min in background).

---

## Step 4 — Keep Render awake (optional, still free)

Render free services sleep after 15 minutes. Options:

- **Accept cold starts** — fine for a side project
- **GitHub Actions pinger** — included in this repo (`.github/workflows/keep-alive.yml`); uses free GitHub minutes

---

## Step 5 — Stripe (optional, still $0 until you sell)

Only needed when you want to accept payments:

```bash
bash scripts/setup_stripe.sh
```

Add keys in Render dashboard → Environment. Webhook URL:

```
https://YOUR-RENDER-URL.onrender.com/api/billing/webhook
```

---

## Local development (always free)

```bash
cd /Users/souravamseekarmarti/Projects/employerflow
make up          # Docker: http://localhost:8000
# or
bash scripts/run_local.sh
```

---

## Cost comparison

| Setup | Monthly cost |
|-------|-------------|
| **This free stack** | **$0** |
| Railway Hobby + Postgres | ~$5–15 |
| Render Starter + Postgres | ~$14+ |
| Fly.io + Postgres | ~$5+ (card required) |

---

## Troubleshooting

**Cold start slow?** Normal on Render free — wait ~60 seconds after first visit.

**DB connection errors?** Ensure Neon connection string includes `?sslmode=require`.

**Employers count is 0?** Wait 2 minutes after deploy; check Render logs for `[startup] Seeded`.

**Want 24/7 uptime without cold starts?** That requires a paid instance (~$7/mo). Not needed for testing.