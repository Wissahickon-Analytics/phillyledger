#!/bin/sh
# Run a Codex review of a plan, of a pull request, or of a pull request's fix round.
#
#   run.sh plan <step | plan-name>
#   run.sh pr <step | plan-name> [base-branch]
#   run.sh fix <step | plan-name> <reviewed-head>
#
# A step is a build step's number, and its plan is docs/plans/step-NN.md. A plan name is the
# name of a file under docs/plans/ without .md, such as standards-sweep-b, for a plan that has no
# entry in design section 15. Its own check table is the check.
#
# Reviews the committed HEAD of the current checkout. Writes Codex's report to
# .codex-review/step-NN-<kind>-<sha>.md, or .codex-review/<plan-name>-<kind>-<sha>.md, and prints
# that path on the last line.
#
# plan runs in a read-only sandbox in this checkout. pr and fix run in a throwaway worktree at
# HEAD with its own synced environment, in a workspace-write sandbox, so Codex can run the
# tests and break code there and not in this checkout.
set -eu

usage() {
    echo "usage: run.sh plan <step | plan-name> | run.sh pr <step | plan-name> [base-branch] | run.sh fix <step | plan-name> <reviewed-head>" >&2
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

root=$(git rev-parse --show-toplevel)
case $step in
'' | step-* | *[!a-z0-9-]*) usage ;;
*[!0-9]*)
    plan=docs/plans/$step.md
    case $(git -C "$root" ls-tree HEAD -- "$plan" | cut -c1-6) in
    100644 | 100755 | 120000) [ -f "$root/$plan" ] ;;
    *) false ;;
    esac || {
        echo "No plan file at $plan in HEAD." >&2
        usage
    }
    nn=
    label=$step
    form=named other=step
    deviations=$(grep -o 'docs/deviations/step-[0-9][0-9]*\.md' "$root/$plan" | sort -u |
        awk '{ printf "%s`%s`", (NR > 1 ? ", " : ""), $0 }')
    ;;
*)
    nn=$(printf '%02d' "$step")
    plan=docs/plans/step-$nn.md
    label=step-$nn
    form=step other=named
    deviations=
    ;;
esac
[ -n "$deviations" ] || deviations=none

command -v codex >/dev/null 2>&1 || {
    echo "codex is not on PATH. Install the Codex CLI and log in, then rerun." >&2
    exit 3
}

if [ -n "$(git -C "$root" status --porcelain)" ]; then
    echo "Uncommitted changes. Codex reviews the committed HEAD, so commit first." >&2
    exit 4
fi
head=$(git -C "$root" rev-parse --verify HEAD)
base_sha=$(git -C "$root" rev-parse --verify --quiet "$base^{commit}") || {
    echo "No commit named $base." >&2
    exit 5
}

common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir)
reference=$(dirname "$(dirname "$common")")/gov-budget-data
[ -d "$reference" ] || {
    echo "No old repository at $reference. It sits beside the folder that holds .git." >&2
    exit 7
}

sha=$(git -C "$root" rev-parse --short=8 "$head")
here=$(cd "$(dirname "$0")" && pwd)
outdir=$root/.codex-review
prompt=$outdir/$label-$kind-$sha.prompt.md
out=$outdir/$label-$kind-$sha.md
base8=$(git -C "$root" rev-parse --short=8 "$base_sha")
prior=$outdir/$label-pr-$base8.md
[ -s "$prior" ] || prior=$outdir/$label-fix-$base8.md
if [ "$kind" = fix ] && [ ! -s "$prior" ]; then
    echo "No report of a pr or fix review of $base8 in $outdir. A fix review answers one, so run it first." >&2
    exit 6
fi
mkdir -p "$outdir"

sed -e "/^{{#$other}}\$/,/^{{\/$other}}\$/d" -e "/^{{[#/]$form}}\$/d" \
    -e "s|{{STEP}}|$step|g" -e "s|{{NN}}|$nn|g" -e "s|{{PLAN}}|$plan|g" \
    -e "s|{{DEVIATIONS}}|$deviations|g" \
    -e "s|{{BASE}}|$base_sha|g" -e "s|{{HEAD}}|$sha|g" -e "s|{{REFERENCE}}|$reference|g" \
    -e "s|{{PRIOR}}|$prior|g" \
    "$here/prompts/$kind.md" >"$prompt"

if [ "$kind" = plan ]; then
    workdir=$root
    sandbox=read-only
else
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/phillyledger-review-XXXXXX")
    workdir=$tmp/checkout
    trap 'git -C "$root" worktree remove --force "$workdir" >/dev/null 2>&1 || true; rm -rf "$tmp"' EXIT
    trap 'exit 1' HUP INT TERM
    git -C "$root" worktree add --quiet --detach "$workdir" "$head"
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
