.PHONY: install run dev clean setup help

# Install dependencies
install:
	poetry install

# Run the application
run:
	cd expenses_tracker && poetry run python app.py

# Run in development mode (same as run since Flask debug is already enabled)
dev: run

# Setup project (install dependencies and create .env if it doesn't exist)
setup: install
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env file - please add your OpenAI API key"; fi

# Clean up generated files
clean:
	rm -rf expenses_tracker/uploads/*
	rm -f expenses_tracker/receipts.db
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Show help
help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies with Poetry"
	@echo "  make setup    - Install dependencies and create .env file"
	@echo "  make run      - Run the Flask application"
	@echo "  make dev      - Run in development mode"
	@echo "  make clean    - Clean up generated files and database"
	@echo "  make help     - Show this help message"

# Default target
all: setup