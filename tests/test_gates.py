from pathlib import Path

GATES = (
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run ty check",
    "uv run prek run --all-files",
    "uv run pytest",
)

CI_WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"
CI_HEADER = """\
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  gates:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.14"]
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked
      - name: Python version
        run: |
          version=$(uv run python -c 'import sys; print(*sys.version_info[:2], sep=".")')
          echo "$version"
          test "$version" = "${{ matrix.python-version }}"
"""
ALWAYS = "${{ !cancelled() }}"


def test_ci_runs_every_gate() -> None:
    steps = "".join(f"      - if: {ALWAYS}\n        run: {gate}\n" for gate in GATES)
    assert CI_WORKFLOW.read_bytes().decode() == CI_HEADER + steps
