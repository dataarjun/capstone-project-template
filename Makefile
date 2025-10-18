.PHONY: help install install-dev setup-env run test lint format clean docker-build docker-up docker-down init-db

help: ## Show this help message
	@echo "Multi-Agent AML Investigation System"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	poetry install --only=main

install-dev: ## Install all dependencies including dev
	poetry install

setup-env: ## Set up environment and install dependencies
	poetry install
	poetry run pre-commit install
	@echo "Environment setup complete!"
	@echo "Don't forget to:"
	@echo "1. Copy env.example to .env"
	@echo "2. Edit .env with your API keys"
	@echo "3. Run 'make init-db' to initialize the database"

run: ## Run the FastAPI application
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

start: ## Start the server using start_server.py
	python start_server.py

start-auto: ## Start the server with automatic port detection
	python start_server.py --auto-port

start-kill: ## Start the server and kill processes on port 8000
	python start_server.py --kill-port

cleanup-ports: ## Clean up processes using development ports
	python cleanup_ports.py

run-prod: ## Run the FastAPI application in production mode
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linting
	poetry run flake8 app tests
	poetry run mypy app

format: ## Format code
	poetry run black app tests
	poetry run isort app tests

format-check: ## Check code formatting
	poetry run black --check app tests
	poetry run isort --check-only app tests

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

init-db: ## Initialize the database
	poetry run python -m app.db.init_db

docker-build: ## Build Docker image
	docker build -t multi-agent-aml-system .

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose services
	docker-compose down

docker-logs: ## View Docker Compose logs
	docker-compose logs -f backend

docker-reset: ## Reset Docker environment
	docker-compose down -v
	docker-compose up -d --build

dev-setup: install-dev setup-env ## Complete development setup
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the application"

prod-setup: install ## Production setup
	@echo "Production environment ready!"
	@echo "Run 'make run-prod' to start the application"
