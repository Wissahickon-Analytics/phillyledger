import re
from pathlib import Path

GATES = (
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run ty check",
    "uv run prek run --all-files",
    "uv run pytest",
)

CI_WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"
ALWAYS = "${{ !cancelled() }}"


def test_ci_runs_every_gate() -> None:
    text = CI_WORKFLOW.read_text()
    lines = {line.strip().removeprefix("- ") for line in text.splitlines()}
    missing = [gate for gate in GATES if f"run: {gate}" not in lines]
    assert not missing, f"ci.yml has no step for {missing}"
    on_block = re.search(r"^on:[ \t]*\n((?:[ \t]+.*\n|[ \t]*\n)*)", text, re.MULTILINE)
    trigger = re.search(
        r"^( +)pull_request:[ \t]*(?:#.*)?\n(?:[ \t]*(?:#.*)?\n)*(\1 +\S.*)?",
        on_block[1] if on_block else "",
        re.MULTILINE,
    )
    assert trigger, "ci.yml has no bare pull_request: trigger in its on: block"
    assert not trigger[2], (
        f"ci.yml filters pull_request with {trigger[2].strip()!r}, so some pull requests get no CI"
    )
    for escape in ("continue-on-error", "github.event_name"):
        assert escape not in text, f"ci.yml uses {escape}, which can let a failed gate pass"
    conditions = re.findall(r"^\s*(?:- )?if:\s*(.*?)\s*$", text, re.MULTILINE)
    others = [condition for condition in conditions if condition != ALWAYS]
    assert not others, f"ci.yml has a step condition other than {ALWAYS}: {others}"
