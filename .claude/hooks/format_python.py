"""PostToolUse hook: run ruff format on a Python file Claude just wrote or edited.

Does nothing until step 1 has created pyproject.toml, and never blocks: lint and type errors are
caught by the step's checks and by prek, not here.
"""

import json
import os
import shutil
import subprocess
import sys


def main() -> int:
    """Format the edited file when it is Python and the workspace exists."""
    data = json.load(sys.stdin)
    path = (data.get("tool_input", {}) or {}).get("file_path", "")
    root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    if not path.endswith(".py") or not os.path.exists(os.path.join(root, "pyproject.toml")):
        return 0
    if shutil.which("uv") is None:
        return 0
    subprocess.run(
        ["uv", "run", "--quiet", "ruff", "format", "--quiet", path],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
