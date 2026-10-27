.PHONY: setup dev test lint typecheck migrate build docker-up docker-down

setup:
	uv venv --python 3.12 .venv
	uv pip install -e ".[api,dev]"
	uv pip install email-validator
	cd apps/web && npm install --ignore-scripts

dev-api:
	uv run uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

test:
	uv run pytest -v

test-engine:
	uv run pytest tests/engine -v

test-api:
	uv run pytest tests/api -v

migrate:
	uv run alembic upgrade head

build:
	cd apps/web && npm run build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
