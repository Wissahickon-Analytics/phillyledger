"""PreToolUse hook: block changes to the gov-budget-data reference checkout.

Claude Code passes the tool call as JSON on stdin. Exit code 2 blocks the call and sends the
message on stderr back to Claude. Reads are never blocked.
"""

import json
import os
import re
import shlex
import sys

REFERENCE = "gov-budget-data"
MESSAGE = (
    "Blocked: ../gov-budget-data is a read-only reference (CLAUDE.md, hard rule 1). "
    "Read from it; write the change in this repo instead."
)

# git subcommands that change a working tree, index, refs or remote.
GIT_WRITES = {
    "add", "am", "apply", "checkout", "cherry-pick", "clean", "commit", "fetch", "merge", "mv",
    "pull", "push", "rebase", "reset", "restore", "revert", "rm", "switch", "worktree",
}
GIT_SUBCOMMAND_WRITES = {"stash": {"push", "pop", "apply", "drop", "clear", "save", ""},
                         "branch": {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move"},
                         "tag": {"-d", "--delete", "-a", "-s", "-f"}}
SHELL_WRITES = re.compile(r"(\bsed\s+-i|\brm\s|\btouch\s|\bmkdir\s|\btruncate\s|\bchmod\s|\bchown\s)")
REDIRECT_INTO = re.compile(r">>?\s*\S*" + re.escape(REFERENCE))
TEE_INTO = re.compile(r"\btee\b[^|;&]*" + re.escape(REFERENCE))
COPY_OR_MOVE = re.compile(r"\b(cp|mv|rsync|ln|install)\b(?P<args>[^;&|]*)")
CD_INTO = re.compile(r"\b(cd|pushd)\s+\S*" + re.escape(REFERENCE))


def inside_reference(path: str) -> bool:
    """Return whether a path resolves into a directory named gov-budget-data."""
    return REFERENCE in os.path.realpath(path).split(os.sep)


def git_write(tokens: list[str], in_reference: bool) -> bool:
    """Return whether a tokenized git command writes to the reference checkout."""
    i = 1
    targets_reference = in_reference
    while i < len(tokens) and tokens[i].startswith("-"):
        option = tokens[i]
        if option in ("-C", "-c", "--git-dir", "--work-tree") and i + 1 < len(tokens):
            if option != "-c" and REFERENCE in tokens[i + 1]:
                targets_reference = True
            i += 2
            continue
        if option.startswith(("--git-dir=", "--work-tree=")) and REFERENCE in option:
            targets_reference = True
        i += 1
    if not targets_reference or i >= len(tokens):
        return False
    sub, rest = tokens[i], tokens[i + 1 :]
    if sub in GIT_WRITES:
        return True
    if sub in GIT_SUBCOMMAND_WRITES:
        first = rest[0] if rest else ""
        if sub == "branch" and first and not first.startswith("-"):
            return True
        return first in GIT_SUBCOMMAND_WRITES[sub]
    return False


def shell_writes_reference(command: str) -> bool:
    """Return whether a shell command looks like it writes into the reference checkout."""
    if REFERENCE not in command:
        return False
    in_reference = False
    for segment in re.split(r"&&|\|\||;|\n|\|", command):
        if CD_INTO.search(segment):
            in_reference = True
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        if tokens and tokens[0] == "git" and git_write(tokens, in_reference):
            return True
        if REFERENCE not in segment and not in_reference:
            continue
        if REDIRECT_INTO.search(segment) or TEE_INTO.search(segment):
            return True
        if SHELL_WRITES.search(segment):
            return True
        copy = COPY_OR_MOVE.search(segment)
        if copy:
            args = copy.group("args").split()
            if args and (REFERENCE in args[-1] or (in_reference and copy.group(1) == "mv")):
                return True
    return False


def main() -> int:
    """Read the hook input and block writes to the reference checkout."""
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    if tool == "Bash":
        if shell_writes_reference(tool_input.get("command", "")):
            print(MESSAGE, file=sys.stderr)
            return 2
        return 0
    if tool not in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        return 0
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if path and inside_reference(path):
        print(MESSAGE, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
