PYTHON := .venv/Scripts/python.exe

.PHONY: setup install run dev test lint format db-up db-down db-logs db-check monitor-up monitor-down monitor-logs cache-up cache-down cache-logs

setup:
	@"$(PYTHON)" -m venv .venv
	@"$(PYTHON)" -m pip install --upgrade pip
	@"$(PYTHON)" -m pip install -r requirements.txt

install:
	@"$(PYTHON)" -m pip install -r requirements.txt

run:
	@"$(PYTHON)" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	@"$(PYTHON)" -m uvicorn app.main:app --reload

test:
	@"$(PYTHON)" -m pytest -q

lint:
	@"$(PYTHON)" -m flake8 app tests

format:
	@"$(PYTHON)" -m black app tests

db-up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d postgres

db-down:
	docker compose --env-file .env -f docker/docker-compose.yml down

db-logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f postgres

db-check:
	@"$(PYTHON)" -m scripts.check_db

monitor-up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d prometheus grafana

monitor-down:
	docker compose --env-file .env -f docker/docker-compose.yml stop prometheus grafana

monitor-logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f prometheus grafana

cache-up:
	docker compose --env-file .env -f docker/docker-compose.yml up -d redis

cache-down:
	docker compose --env-file .env -f docker/docker-compose.yml stop redis

cache-logs:
	docker compose --env-file .env -f docker/docker-compose.yml logs -f redis
