# Show the recipes
default:
    @just --list

# Install the locked environment
sync:
    uv sync --locked

# Run the tests. Extra arguments go to pytest, as in `just test tests/test_gates.py -k just`
test *ARGS:
    uv run pytest {{ARGS}}

# Lint, format check, types and import contracts. Changes no file
check:
    uv run ruff check .
    uv run ruff format --check .
    uv run ty check
    uv run lint-imports

# Fix what ruff can fix, then format
fix:
    uv run ruff check --fix .
    uv run ruff format .

# The six gates that CI runs
gates: check
    uv run prek run --all-files
    uv run pytest
