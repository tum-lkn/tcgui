
file_finder = find . -type f $(1) -not -path './venv/*'

PY_FILES = $(call file_finder,-name "*.py")

format:
	$(PY_FILES) | xargs black

check_format:
	$(PY_FILES) | xargs black --diff --check
