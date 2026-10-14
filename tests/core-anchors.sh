#!/usr/bin/env bash
# Checks that a core speckit-implement skill still carries every rule the
# fragment narrows by name and every step the worker's brief points at. If
# upstream drops or rewords one, the fragment refers to nothing and has to be
# revised (constitution I).
#
# Usage:  tests/core-anchors.sh <skill-file>
# Exit:   0 every anchor present; 1 one or more missing, each named; 2 usage
set -euo pipefail

[ "$#" -eq 1 ] && [ -r "$1" ] || {
  echo "usage: tests/core-anchors.sh <readable skill file>" >&2
  exit 2
}

# One line, runs of whitespace squeezed: a rewrap upstream is not a rewording.
text=$(tr -s '[:space:]' ' ' < "$1")

anchors=(
  # Narrowed by the fragment
  'For completed tasks, make sure to mark the task off as [X]'
  'parallel tasks [P] can run together'
  'Halt execution if any non-parallel task fails'
  # Named in the worker's brief
  'Load and analyze the implementation context'
  'Project Setup Verification'
  'Execute implementation'
  'Implementation execution rules'
  'Progress tracking and error handling'
)

missing=0
for anchor in "${anchors[@]}"; do
  # Fixed strings: [X] and [P] are not character classes here.
  grep -qF -- "$anchor" <<< "$text" || {
    echo "FAIL: core speckit-implement no longer says '$anchor'; revise the fragment"
    missing=1
  }
done
exit "$missing"
