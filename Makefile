PYTHON := .venv/Scripts/python.exe

.PHONY: setup install run dev test lint format

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
