.PHONY: help up down logs build rebuild test test-unit test-integration train fmt lint clean

help:
	@echo "Targets:"
	@echo "  up                 docker compose up -d --build"
	@echo "  down               docker compose down"
	@echo "  logs               docker compose logs -f"
	@echo "  build              docker compose build"
	@echo "  rebuild            docker compose build --no-cache"
	@echo "  train              train ML model into ml-engine/model_store"
	@echo "  test               run all tests (unit + integration)"
	@echo "  test-unit          run unit tests only"
	@echo "  test-integration   bring up test stack and run integration tests"
	@echo "  fmt                run ruff format on python sources"
	@echo "  lint               run ruff check on python sources"

up:
	docker compose --env-file .env up -d --build

down:
	docker compose --env-file .env down

logs:
	docker compose logs -f --tail=100

build:
	docker compose --env-file .env build

rebuild:
	docker compose --env-file .env build --no-cache

train:
	cd ml-engine && python -m app.models.train --data datasets/sample_jobs.csv --out model_store/

test: test-unit test-integration

test-unit:
	cd ml-engine && pytest -q
	cd mcp-servers/auth && pytest -q
	cd mcp-servers/database && pytest -q
	cd mcp-servers/memory && pytest -q
	cd backend && pytest -q

test-integration:
	docker compose --env-file .env up -d --build
	pytest -q tests/integration

fmt:
	ruff format backend ml-engine mcp-servers tests

lint:
	ruff check backend ml-engine mcp-servers tests

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	rm -rf ml-engine/model_store/*.joblib ml-engine/model_store/manifest.json
