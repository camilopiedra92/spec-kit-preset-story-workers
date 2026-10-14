#!/usr/bin/env bash
# One confirmed step of the eval (research R11): three counted runs of each
# named arm, arms alternating per round, each run tried at most three times.
# A try counts against that bound only once it reached the agent (it left a
# stream): a refusal that spent nothing can be fixed and the step run again,
# and a run already counted is not run again.
# Before every try: the attempt's probes passed on the installed Claude Code
# version, and for `with` or `fallback` the difficulty gate is open. State
# lives in the attempt directory, so each step is one command.
#
# Usage:  tests/eval/runs.sh <attempt-dir> <fixture> <arm>...
# Exit:   0 every run counted; 1 a run had three tries without counting (the
#         eval stops, not measured); 2 refused (a try's status says why)
#
# The contract is specs/002-large-phase-remeasure/contracts/harness.md.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
refuse() {
  echo "runs.sh: $*" >&2
  exit 2
}
[ "$#" -ge 3 ] || refuse "usage: tests/eval/runs.sh <attempt-dir> <fixture> <arm>..."
attempt=$1
fixture=$2
shift 2
arms=("$@")
seen=" "
for arm in "${arms[@]}"; do
  case $arm in without | with | fallback) ;; *) refuse "unknown arm '$arm'" ;; esac
  case $seen in *" $arm "*) refuse "arm '$arm' named twice" ;; esac
  seen="$seen$arm "
done
# The without set decides the gate the others need (FR-003, FR-007).
[ "${#arms[@]}" -eq 1 ] || case $seen in *" without "*) refuse "without runs alone" ;; esac
[ -d "$attempt" ] || refuse "no attempt directory $attempt"

refused() { # <try-dir> <reason>: the reason in the try's status, exit 2
  mkdir -p "$1"
  [ -s "$1/status" ] || echo "refused: $2" > "$1/status"
  echo "runs.sh: $(cat "$1/status")" >&2
  exit 2
}
version() { grep -m1 -oE '[0-9]+\.[0-9]+\.[0-9]+' || true; }
checks() { # <try-dir> <arm>: the probes, then the gate
  local try=$1 arm=$2 probes=$attempt/probes.txt installed
  [ -f "$probes" ] || refused "$try" "no probes.txt in $attempt: run the probes first"
  ! grep -q '^FAIL' "$probes" || refused "$try" "a probe failed in $probes"
  # probes.sh's closing summary: a file cut short has none.
  grep -qE '^probes: [1-9][0-9]* ok, 0 FAIL$' "$probes" ||
    refused "$try" "no probe summary in $probes: rerun the probes"
  installed=$(DISABLE_AUTOUPDATER=1 claude --version | version)
  [ "$(head -n 1 "$probes" | version)" = "$installed" ] ||
    refused "$try" "Claude Code version $installed is not the probes' $(head -n 1 "$probes" | version)"
  if [ "$arm" != without ]; then
    local gate
    gate=$(python3 "$here/compare.py" --gate "$attempt"/without-1 "$attempt"/without-2 \
      "$attempt"/without-3 2>&1) ||
      refused "$try" "the gate is not open on $attempt's without runs: ${gate##*$'\n'}"
  fi
}

errors=$(mktemp)
trap 'rm -f "$errors"' EXIT
one_run() { # <arm> <n>: tries until one counts
  local arm=$1 n=$2 try=0 spent=0 dir rc base=() old
  [ ! -L "$attempt/$arm-$n" ] || return 0
  # The tries an earlier invocation left: those with a stream spent usage.
  for old in "$attempt/$arm-$n"-*; do
    [ -d "$old" ] || continue
    try=$((try + 1))
    [ ! -e "$old/stream.jsonl" ] || spent=$((spent + 1))
  done
  [ ! -e "$attempt/without-1" ] || base=(--baseline "$attempt/without-1")
  while [ "$spent" -lt 3 ]; do
    try=$((try + 1))
    dir=$attempt/$arm-$n-$try
    checks "$dir" "$arm"
    rc=0
    # run.sh's stderr kept, then shown: a refusal before it creates the try's
    # directory says why only there. (Not a tee: tail could read it unfinished.)
    "$here/run.sh" ${base[@]+"${base[@]}"} "$fixture" "$arm" "$dir" 2> "$errors" || rc=$?
    cat "$errors" >&2
    [ ! -e "$dir/stream.jsonl" ] || spent=$((spent + 1))
    case $rc in
      0)
        (cd "$attempt" && ln -s "$arm-$n-$try" "$arm-$n")
        return 0
        ;;
      1) ;;
      *) refused "$dir" "run.sh exit $rc: $(tail -n 1 "$errors")" ;;
    esac
  done
  echo "runs.sh: $arm run $n: three tries without a counted run; the eval stops" >&2
  exit 1
}

for n in 1 2 3; do
  for arm in "${arms[@]}"; do
    one_run "$arm" "$n"
  done
done
