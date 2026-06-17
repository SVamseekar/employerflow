# EmployerFlow — Deployment Status

**Last deployed:** 2026-06-17

## Production (Render Free + Neon Free) — LIVE

| Resource | URL |
|----------|-----|
| **App** | https://employerflow-api.onrender.com |
| **Landing** | https://employerflow-api.onrender.com/ |
| **Dashboard** | https://employerflow-api.onrender.com/app.html |
| **API Health** | https://employerflow-api.onrender.com/api/health |
| **GitHub** | https://github.com/SVamseekar/employerflow |
| **Render Dashboard** | https://dashboard.render.com/web/srv-d8p9tjb7uimc739vl2o0 |
| **Neon Dashboard** | https://console.neon.tech (project: employerflow) |

**Cost:** $0/month (Render Free + Neon Free)

**Database:** 14,674 employers seeded in Neon Postgres

**Note:** Render free tier spins down after 15 min idle (~60s cold start). GitHub Actions keep-alive workflow pings every 14 min.

---

## Local (free)

```bash
make up    # http://localhost:8000
```

---

## Tear down Railway (avoid charges)

If you still have the old Railway project, delete it:
https://railway.com/project/7bb7f581-02b0-4370-a933-d07c34117cbc

---

## Stripe (optional)

Webhook URL: `https://employerflow-api.onrender.com/api/billing/webhook`

Set keys in Render dashboard → employerflow-api → Environment.