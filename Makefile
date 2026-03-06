# Variables
PY = python3
VENV = .venv
BIN = $(VENV)/bin

# Code directories for linting
CODE_DIRS = src tests

.PHONY: install run debug lint lint-strict test clean

# --- Setup ---

install:
	@echo "--- 1. Creating/Updating Virtual Environment ---"
	@if [ ! -d "$(VENV)" ]; then $(PY) -m venv $(VENV); fi
	@$(BIN)/pip install -U pip
	@$(BIN)/pip install -r requirements.txt
	@$(BIN)/pip install flake8 mypy types-regex
	@echo "--- Setup Complete! ---"

# --- Execution ---

run:
ifndef MAP
	$(error Usage: make run MAP=<path/to/map.txt>)
endif
	PYTHONPATH=. $(BIN)/python3 src/main.py $(MAP)

visual:
	PYTHONPATH=. python3 src/visualizer.py $(MAP)
debug:  # to define
ifndef MAP
	$(error Usage: make debug MAP=<path/to/map.txt>)
endif
	PYTHONPATH=. $(BIN)/python3 -m logging -v src/main.py $(MAP)

# --- Quality Assurance ---

lint:
	@echo "--- Running Flake8 ---"
	$(BIN)/flake8 $(CODE_DIRS)
	@echo "--- Running Mypy ---"
	PYTHONPATH=. $(BIN)/mypy $(CODE_DIRS) \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs \
		--warn-return-any \
		--warn-unused-ignores

lint-strict:
	@echo "--- Running Strict Linting ---"
	$(BIN)/flake8 $(CODE_DIRS)
	PYTHONPATH=. $(BIN)/mypy $(CODE_DIRS) --strict

# --- Testing ---

test:
ifndef ARGS
	$(error Usage: make test ARGS="<path/to/map.txt> [k_paths]")
endif
	@echo "--- Running Integration Tests ---"
	PYTHONPATH=. $(BIN)/python3 tests/parser_tester.py $(ARGS)

# --- Cleanup ---

clean:
	rm -rf .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "--- Cleanup Complete ---"