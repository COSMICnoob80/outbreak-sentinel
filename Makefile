.PHONY: up down logs test run

PY ?= env -u PYTHONPATH .venv/bin/python
COMPOSE ?= docker compose

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

test:
	$(PY) -m pytest -q

run:
	$(PY) -m uvicorn app:app --host 0.0.0.0 --port 8000
