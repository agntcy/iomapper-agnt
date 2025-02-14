PROJECT_NAME := agntcy_iomapper
DOCKER_IMAGE=$(PROJECT_NAME)
DOCKER_TAG=latest
GIT_COMMIT=$(shell git rev-parse HEAD)

CURL_AGENT=curl --no-progress-meter \
	-H 'accept: application/json' \
	-H 'content-type: application/json'

.PHONY: run setup setup_sanity default check
default: check

# ============================

check: setup_check lint_check format_check type_check

lint_check: setup_sanity
	poetry run ruff check ./$(PROJECT_NAME)

lint_fix: setup_sanity
	poetry run ruff check --fix ./$(PROJECT_NAME)

format_check: setup_sanity
	poetry run ruff format --diff ./$(PROJECT_NAME)

format_fix: setup_sanity
	poetry run ruff format ./$(PROJECT_NAME)

type_check: setup_sanity
	poetry run mypy --config-file ../../.rules/mypy.ini ./$(PROJECT_NAME) || echo "Ignoring mypy failure"

setup_sanity:
	poetry install --only sanity --no-root

set_python_env:
	poetry env use python3.12

setup_check: set_python_env setup_sanity
	poetry run mypy --config-file ../../.rules/mypy.ini --install-types --non-interactive ./$(PROJECT_NAME) || echo "Ignoring mypy failure"

setup: set_python_env
	poetry install --no-root

# ============================

setup_test: set_python_env
	@poetry install --with=test

test: setup_test
	poetry run pytest -vvrx
