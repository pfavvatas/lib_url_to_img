# lib_url_to_img Makefile
# Common tasks for project management

.PHONY: help install run clean test lint format

# Default target
help:
	@echo "🚀 lib_url_to_img - Available Commands:"
	@echo "======================================"
	@echo "make install    - Set up the project environment"
	@echo "make run        - Start all services"
	@echo "make run-python - Start Python components only"
	@echo "make clean      - Clean up generated files"
	@echo "make test       - Run tests"
	@echo "make lint       - Run code linting"
	@echo "make format     - Format code"
	@echo ""
	@echo "Quick start: make install && make run"

# Install dependencies
install:
	@echo "🔧 Setting up project environment..."
	@python run_project.py --setup-only 2>/dev/null || python -c "from run_project import ProjectLauncher; launcher = ProjectLauncher(); launcher.setup_python_env(); print('✅ Python environment ready')"

# Run the full project
run:
	@echo "🚀 Starting lib_url_to_img project..."
	@python run_project.py

# Run Python components only
run-python:
	@echo "🐍 Starting Python API only..."
	@cd backend/api && \
	if [ ! -d ".venv" ]; then python -m venv .venv; fi && \
	source .venv/bin/activate && \
	pip install -r requirements.txt && \
	python main.py

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf backend/api/results* 2>/dev/null || true
	@rm -rf backend/api/output_html_files/* 2>/dev/null || true
	@echo "✅ Clean complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd backend/api && \
	source .venv/bin/activate && \
	python -m pytest tests/ -v 2>/dev/null || echo "No tests found or pytest not installed"

# Lint code
lint:
	@echo "🔍 Running code linting..."
	@cd backend/api && \
	source .venv/bin/activate && \
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics 2>/dev/null || echo "flake8 not installed"

# Format code
format:
	@echo "🎨 Formatting code..."
	@cd backend/api && \
	source .venv/bin/activate && \
	black . 2>/dev/null || echo "black not installed"

# Development setup
dev-setup: install
	@echo "💻 Setting up development environment..."
	@cd backend/api && source .venv/bin/activate && pip install pytest black flake8
	@cd frontend && npm install 2>/dev/null || echo "npm not available"
	@echo "✅ Development environment ready" 