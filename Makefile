# Hendrix Video Analysis Pipeline - Makefile
# Common development and deployment commands

.PHONY: help install install-dev test clean docker docker-run format lint verify

# Default target
help:
	@echo "🎬 Hendrix Video Analysis Pipeline"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@echo "  install      - Install hendrix package"
	@echo "  install-dev  - Install in development mode with dev dependencies"
	@echo "  install-all  - Install all optional dependencies"
	@echo "  test         - Run tests"
	@echo "  format       - Format code with black and ruff"
	@echo "  lint         - Lint code with ruff"
	@echo "  verify       - Verify installation"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker       - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  example      - Run example analysis"
	@echo ""

# Installation targets
install:
	@echo "📦 Installing Hendrix..."
	pip install -e .

install-dev:
	@echo "🔧 Installing Hendrix in development mode..."
	pip install -e ".[dev]"

install-all:
	@echo "📦 Installing Hendrix with all dependencies..."
	pip install -e ".[all]"

# Testing
test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

test-quick:
	@echo "⚡ Running quick tests..."
	python -m pytest tests/ -x --tb=short

# Code quality
format:
	@echo "🎨 Formatting code..."
	black hendrix/ tests/
	ruff check hendrix/ tests/ --fix

lint:
	@echo "🔍 Linting code..."
	ruff check hendrix/ tests/
	mypy hendrix/ --ignore-missing-imports

# Verification
verify:
	@echo "✅ Verifying installation..."
	hendrix verify

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Docker
docker:
	@echo "🐳 Building Docker image..."
	docker build -t hendrix-video:latest .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -it --rm -v $$(pwd)/data:/app/data -v $$(pwd)/outputs:/app/outputs hendrix-video:latest

docker-compose-up:
	@echo "🐳 Starting Docker Compose..."
	docker-compose up -d

# Examples
example: 
	@echo "🎬 Running example analysis..."
	@if [ ! -f "test_video.mp4" ]; then \
		echo "❌ test_video.mp4 not found. Please add a test video file."; \
		exit 1; \
	fi
	hendrix analyze test_video.mp4 --profile test

example-docker:
	@echo "🐳 Running example with Docker..."
	@if [ ! -f "data/test_video.mp4" ]; then \
		echo "❌ data/test_video.mp4 not found. Please add a test video file to the data/ directory."; \
		exit 1; \
	fi
	docker run --rm -v $$(pwd)/data:/app/data -v $$(pwd)/outputs:/app/outputs hendrix-video:latest analyze /app/data/test_video.mp4

# Development helpers
requirements:
	@echo "📋 Generating requirements.txt from pyproject.toml..."
	pip-compile pyproject.toml

init-dev:
	@echo "🚀 Setting up development environment..."
	pip install --upgrade pip setuptools wheel
	$(MAKE) install-dev
	@if [ -d ".git" ]; then \
		pre-commit install; \
		echo "✅ Pre-commit hooks installed"; \
	fi
	@echo "✅ Development environment ready!"

# Release helpers
check-release:
	@echo "🔍 Checking release readiness..."
	python -m build --check
	twine check dist/*

build:
	@echo "🏗️  Building package..."
	python -m build

# Quick start
quickstart: install verify example
	@echo ""
	@echo "🎉 Quickstart complete!"
	@echo "Try: hendrix analyze your_video.mp4"