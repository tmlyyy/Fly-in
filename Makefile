PYTHON ?= python3
VENV ?= .venv
VENV_FLAGS ?=
PY = $(VENV)/bin/python
MAP ?= maps/easy/01_linear_path.txt
ARGS ?=

.PHONY: install run debug clean lint

install:
	$(PYTHON) -m venv $(VENV_FLAGS) $(VENV)
	$(PY) -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

run:
	$(PY) fly_in.py "$(MAP)" $(ARGS)

debug:
	$(PY) -m pdb fly_in.py "$(MAP)" $(ARGS)

clean:
	find . -path './$(VENV)' -prune -o -type d \( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache \) -prune -exec rm -rf {} +

lint:
	$(PY) -m flake8 .
	$(PY) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
