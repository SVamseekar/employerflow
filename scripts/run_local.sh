#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

export DATABASE_URL="${DATABASE_URL:-sqlite:///${ROOT}/data/employerflow.db}"
export APP_URL="${APP_URL:-http://localhost:8000}"
export SECRET_KEY="${SECRET_KEY:-dev-secret-change-in-production}"

mkdir -p "$ROOT/data"
.venv/bin/python ../scripts/import_employers.py 2>/dev/null || true

echo "Starting EmployerFlow at http://localhost:8000"
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload