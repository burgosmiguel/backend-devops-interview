.DEFAULT_GOAL := help

.PHONY: help dev build seed test shell logs down lint

help:
	@echo "Usage:"
	@echo "  make dev    Build images, start everything, seed the DB, then tail logs."
	@echo "  make seed   Populate the DB (~600k rows). Runs automatically via 'make dev'."
	@echo "  make test   Run tests inside the container"
	@echo "  make shell  Open a shell in the app container"
	@echo "  make logs   Tail app logs"
	@echo "  make down   Stop and remove containers"
	@echo "  make lint   ruff check + format check"

dev:
	docker compose up --build -d
	docker compose run --rm app uv run python manage.py seed
	docker compose logs -f

build:
	docker compose build

seed:
	docker compose exec app uv run python manage.py seed

test:
	docker compose run --rm app uv run pytest

shell:
	docker compose exec app sh

logs:
	docker compose logs -f app

down:
	docker compose down

lint:
	docker compose run --rm app uv run ruff check .
	docker compose run --rm app uv run ruff format --check .
