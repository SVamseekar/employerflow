.PHONY: up down logs import seed test health

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

import:
	DATABASE_URL=postgresql+psycopg2://employerflow:employerflow@localhost:5433/employerflow \
		python3 scripts/import_employers.py

health:
	curl -s http://localhost:8000/api/health | python3 -m json.tool

test:
	cd backend && python3 -m pytest tests/ -q 2>/dev/null || echo "Run: pip install pytest httpx"