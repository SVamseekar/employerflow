# EmployerFlow — Deployment

## Recommended: 100% free stack

See **[FREE_STACK.md](FREE_STACK.md)** for the full guide.

| Component | Provider | Cost |
|-----------|----------|------|
| API hosting | Render Free | $0 |
| Database | Neon Free | $0 |
| Code | GitHub | $0 |

**Deploy in 2 clicks:** https://dashboard.render.com/select-repo?repo=https://github.com/SVamseekar/employerflow

---

## Local (free)

```bash
make up    # http://localhost:8000
```

---

## Legacy: Railway (NOT free — tear down)

Railway was used during initial deploy. **Delete the project** to avoid charges:

https://railway.com/project/7bb7f581-02b0-4370-a933-d07c34117cbc

Previous URL (will stop working after deletion):
`https://employerflow-api-production.up.railway.app`

---

## Stripe (optional)

No monthly fee — only per-transaction. Configure after Render deploy:

Webhook: `https://YOUR-APP.onrender.com/api/billing/webhook`