#!/bin/sh
# Run a Codex review of a step plan, a step's pull request, or a pull request's fix round.
#
#   run.sh plan <step>
#   run.sh pr <step> [base-branch]
#   run.sh fix <step> <reviewed-head>
#
# Reviews the committed HEAD of the current checkout. Writes Codex's report to
# .codex-review/step-NN-<kind>-<sha>.md and prints that path on the last line.
#
# plan runs in a read-only sandbox in this checkout. pr and fix run in a throwaway worktree at
# HEAD with its own synced environment, in a sandbox that can write only there, so Codex can
# run the tests and break code without touching this checkout.
set -eu

usage() {
    echo "usage: run.sh plan <step> | run.sh pr <step> [base-branch] | run.sh fix <step> <reviewed-head>" >&2
    exit 2
}

[ $# -ge 2 ] || usage
kind=$1
step=$2
case $kind in
plan) base=main ;;
pr) base=${3:-main} ;;
fix)
    [ $# -ge 3 ] || usage
    base=$3
    ;;
*) usage ;;
esac
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
git -C "$root" rev-parse --verify --quiet "$base^{commit}" >/dev/null || {
    echo "No commit named $base." >&2
    exit 5
}

nn=$(printf '%02d' "$step")
sha=$(git -C "$root" rev-parse --short=8 HEAD)
reference=$(cd "$root/.." && pwd)/gov-budget-data
here=$(cd "$(dirname "$0")" && pwd)
outdir=$root/.codex-review
prompt=$outdir/step-$nn-$kind-$sha.prompt.md
out=$outdir/step-$nn-$kind-$sha.md
prior=$outdir/step-$nn-pr-$(git -C "$root" rev-parse --short=8 "$base^{commit}").md
mkdir -p "$outdir"

sed -e "s|{{STEP}}|$step|g" -e "s|{{NN}}|$nn|g" -e "s|{{BASE}}|$base|g" \
    -e "s|{{HEAD}}|$sha|g" -e "s|{{REFERENCE}}|$reference|g" -e "s|{{PRIOR}}|$prior|g" \
    "$here/prompts/$kind.md" >"$prompt"

if [ "$kind" = plan ]; then
    workdir=$root
    sandbox=read-only
else
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/phillyledger-review-XXXXXX")
    workdir=$tmp/checkout
    trap 'git -C "$root" worktree remove --force "$workdir" >/dev/null 2>&1 || true; rm -rf "$tmp"' EXIT
    trap 'exit 1' HUP INT TERM
    git -C "$root" worktree add --quiet --detach "$workdir" HEAD
    (cd "$workdir" && uv sync --locked --quiet)
    sandbox=workspace-write
fi

profile=${CODEX_REVIEW_PROFILE:-phillyledger-review}
codex_home=${CODEX_HOME:-$HOME/.codex}
set -- exec --sandbox "$sandbox" --cd "$workdir" --output-last-message "$out"
if [ -f "$codex_home/$profile.config.toml" ]; then
    set -- "$@" --profile "$profile"
else
    echo "No Codex profile at $codex_home/$profile.config.toml; using Codex's default model." >&2
fi

codex "$@" - <"$prompt"
echo "$out"
