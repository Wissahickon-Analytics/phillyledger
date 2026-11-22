#!/bin/sh
# Run a read-only Codex review of a step plan or a step's pull request.
#
#   run.sh plan <step>
#   run.sh pr <step> [base-branch]
#
# Reviews the committed HEAD of the current checkout. Writes Codex's report to
# .codex-review/step-NN-<kind>-<sha>.md and prints that path on the last line.
set -eu

usage() {
    echo "usage: run.sh plan <step> | run.sh pr <step> [base-branch]" >&2
    exit 2
}

[ $# -ge 2 ] || usage
kind=$1
step=$2
base=${3:-main}
case $kind in plan | pr) ;; *) usage ;; esac
case $step in *[!0-9]* | '') usage ;; esac

command -v codex >/dev/null 2>&1 || {
    echo "codex is not on PATH. Install the Codex CLI and log in, then rerun." >&2
    exit 3
}

root=$(git rev-parse --show-toplevel)
if [ -n "$(git -C "$root" status --porcelain)" ]; then
    echo "Uncommitted changes. Codex reviews the committed HEAD, so commit first." >&2
    exit 4
fi

nn=$(printf '%02d' "$step")
sha=$(git -C "$root" rev-parse --short=8 HEAD)
reference=$(cd "$root/.." && pwd)/gov-budget-data
here=$(cd "$(dirname "$0")" && pwd)
outdir=$root/.codex-review
prompt=$outdir/step-$nn-$kind-$sha.prompt.md
out=$outdir/step-$nn-$kind-$sha.md
mkdir -p "$outdir"

sed -e "s|{{STEP}}|$step|g" -e "s|{{NN}}|$nn|g" -e "s|{{BASE}}|$base|g" \
    -e "s|{{HEAD}}|$sha|g" -e "s|{{REFERENCE}}|$reference|g" \
    "$here/prompts/$kind.md" >"$prompt"

profile=${CODEX_REVIEW_PROFILE:-phillyledger-review}
codex_home=${CODEX_HOME:-$HOME/.codex}
set -- exec --sandbox read-only --cd "$root" --output-last-message "$out"
if [ -f "$codex_home/$profile.config.toml" ]; then
    set -- "$@" --profile "$profile"
else
    echo "No Codex profile at $codex_home/$profile.config.toml; using Codex's default model." >&2
fi

codex "$@" - <"$prompt"
echo "$out"
