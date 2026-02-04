# Makefile for inventory_web

.PHONY: help install dev start-render migrate test lint format

# Use bash as the shell
SHELL := /bin/bash

# Define paths. We run make from the root, so paths are relative to root.
VENV_PYTHON := ./.venv/bin/python
GUNICORN := ./.venv/bin/gunicorn
RUFF := ./.venv/bin/ruff
UV_PATH_PREFIX := PATH=$(HOME)/.local/bin:$$PATH
UV := $(UV_PATH_PREFIX) uv

# Default command is help
default: help

help:
	@echo "Makefile for inventory_web"
	@echo ""
	@echo "Usage:"
	@echo "  make install      - Install dependencies from requirements.txt"
	@echo "  make dev          - Start development server on 0.0.0.0:8000"
	@echo "  make start-render - Start production server with Gunicorn"
	@echo "  make migrate      - Create and apply database migrations"
	@echo "  make test         - Run Django tests"
	@echo "  make lint         - Run ruff linter on the dev directory"
	@echo "  make format       - Run ruff formatter on the dev directory"
	@echo ""

install:
	@echo "Installing dependencies from requirements.txt..."
	cd . && $(UV) pip install -r requirements.txt

dev:
	@echo "Starting development server on 0.0.0.0:8000..."
	$(VENV_PYTHON) ./manage.py runserver 0.0.0.0:8000

start-render:
	@echo "Starting production server with Gunicorn..."
	cd . && $(GUNICORN) inventory_web.wsgi:application

migrate:
	@echo "Creating migrations..."
	$(VENV_PYTHON) ./manage.py makemigrations
	@echo "Applying migrations..."
	$(VENV_PYTHON) ./manage.py migrate

test:
	@echo "Running tests..."
	$(VENV_PYTHON) ./manage.py test

lint:
	@echo "Running linter..."
	$(RUFF) check .

format:
	@echo "Running formatter..."
	$(RUFF) check . --fix