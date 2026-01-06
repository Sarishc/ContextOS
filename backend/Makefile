.PHONY: help build up down restart logs test clean

help: ## Show this help message
	@echo "ContextOS Backend - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	@./scripts/start.sh

down: ## Stop all services
	docker-compose down

down-v: ## Stop all services and remove volumes
	docker-compose down -v

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f api

logs-worker: ## View Celery worker logs only
	docker-compose logs -f celery-worker

test: ## Run API tests
	@./scripts/test.sh

shell-api: ## Open shell in API container
	docker-compose exec api bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec db psql -U contextos -d contextos_db

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

ps: ## Show running containers
	docker-compose ps

clean: ## Clean up containers, volumes, and images
	docker-compose down -v
	docker system prune -f

format: ## Format Python code with black
	docker-compose exec api black app/ main.py

lint: ## Lint Python code with mypy
	docker-compose exec api mypy app/ main.py

install-dev: ## Install development dependencies locally
	pip install -r requirements.txt
	pip install black mypy

dev: ## Run API in development mode (locally)
	python main.py

worker: ## Run Celery worker (locally)
	celery -A app.services.celery_app worker --loglevel=info

flower: ## Run Flower (locally)
	celery -A app.services.celery_app flower

