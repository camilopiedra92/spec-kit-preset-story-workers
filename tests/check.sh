#!/usr/bin/env bash
# The one command CI runs and every change runs before it is called done.
# Stops at the first failing step and names it.
#
# Usage:  tests/check.sh        from the repository root
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

step() {
  "$@" || {
    echo "FAIL: $*"
    exit 1
  }
}

step tests/compose.sh
