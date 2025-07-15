# Makefile for Aiayer

.PHONY: help install install-dev test test-cov lint format clean build docker-build docker-run docker-stop setup config-validate

# Default target
help:
	@echo "Available commands:"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Clean build artifacts"
	@echo "  build          - Build the application"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run Docker container"
	@echo "  docker-stop    - Stop Docker container"
	@echo "  setup          - Initial setup"
	@echo "  config-validate - Validate configuration"

# Installation
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov flake8 black isort bandit safety
	python -m spacy download en_core_web_sm

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing -v

# Code quality
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	bandit -r . -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true

format:
	black .
	isort .

# Cleaning
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.log
	rm -rf logs/
	rm -rf cache/
	rm -rf pids/

# Building
build:
	python setup.py build

# Docker commands
docker-build:
	docker build -t aiayer .

docker-run:
	docker run -d \
		--name aiayer \
		-p 5000:5000 \
		-p 5001:5001 \
		-p 8765:8765 \
		-v $(PWD)/config:/app/config \
		aiayer

docker-stop:
	docker stop aiayer || true
	docker rm aiayer || true

# Setup
setup:
	@echo "Setting up Aiayer..."
	mkdir -p logs cache pids memory config/backups
	chmod +x main.py setup_project.sh
	@echo "Setup complete!"

# Configuration
config-validate:
	python -c "from utils.config_validator import ConfigValidator; validator = ConfigValidator(); print('Configuration is valid!' if validator.validate() else 'Configuration has errors!')"

# Development helpers
dev:
	python main.py --debug

run:
	python main.py

# Systemd service (Linux)
install-service:
	sudo cp systemd/aiayer.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable aiayer

start-service:
	sudo systemctl start aiayer

stop-service:
	sudo systemctl stop aiayer

status-service:
	sudo systemctl status aiayer

# Backup and restore
backup-config:
	tar -czf config_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz config/

restore-config:
	@echo "Usage: make restore-config BACKUP_FILE=config_backup_YYYYMMDD_HHMMSS.tar.gz"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE"; exit 1; fi
	tar -xzf $(BACKUP_FILE)

# Security checks
security-scan:
	bandit -r . -f json -o bandit-report.json
	safety check --json --output safety-report.json
	@echo "Security scan completed. Check bandit-report.json and safety-report.json"

# Documentation
docs-build:
	cd docs && make html

docs-serve:
	cd docs/_build/html && python -m http.server 8000

# Release helpers
version:
	@echo "Current version: $(shell python -c "import setup; print(setup.setup()['version'])")"

bump-patch:
	@echo "Bumping patch version..."
	@python -c "import re; content=open('setup.py').read(); new_content=re.sub(r'version=\"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version=\"{m.group(1)}.{m.group(2)}.{int(m.group(3))+1}\"', content); open('setup.py', 'w').write(new_content)"

bump-minor:
	@echo "Bumping minor version..."
	@python -c "import re; content=open('setup.py').read(); new_content=re.sub(r'version=\"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version=\"{m.group(1)}.{int(m.group(2))+1}.0\"', content); open('setup.py', 'w').write(new_content)"

bump-major:
	@echo "Bumping major version..."
	@python -c "import re; content=open('setup.py').read(); new_content=re.sub(r'version=\"(\d+)\.(\d+)\.(\d+)\"', lambda m: f'version=\"{int(m.group(1))+1}.0.0\"', content); open('setup.py', 'w').write(new_content)"

# Monitoring
logs:
	tail -f logs/aiayer.log

logs-clear:
	> logs/aiayer.log

# Performance
profile:
	python -m cProfile -o profile.stats main.py

profile-view:
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Environment
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

venv-clean:
	rm -rf venv/

# Database
db-init:
	@echo "Initializing database..."
	@python -c "from memory.memory_system import MemorySystem; import asyncio; asyncio.run(MemorySystem().initialize())"

db-clean:
	rm -rf memory/*.db
	rm -rf memory/*.sqlite*

# All-in-one commands
full-test: lint test test-cov security-scan
	@echo "Full test suite completed!"

full-clean: clean venv-clean db-clean
	@echo "Full cleanup completed!"

full-setup: setup install-dev config-validate
	@echo "Full setup completed!" 