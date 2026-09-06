.PHONY: help build up down test clean lint

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make test     - Run all tests"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make lint     - Run linters"

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

test:
	docker compose exec backend pytest
	docker compose exec frontend npm test

clean:
	docker compose down -v
	rm -rf backend/__pycache__ backend/.pytest_cache

lint:
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint
