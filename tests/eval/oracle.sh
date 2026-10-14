#!/usr/bin/env bash
# A fixture's oracle proof: its held-out tests, run as run.sh runs them, against
# its reference implementation laid over its project, all as committed. The
# fixture's held-out total N (data model, "Held-out score") is the count
# collected here; every test must pass and the count must equal heldout/N.
#
# Usage:  tests/eval/oracle.sh [--write-n] <fixture>
#         --write-n records the collected count as heldout/N instead of
#         checking it (commit the file afterwards)
# Exit:   0 every test passed and the count is N; 1 otherwise; 2 refused
#
# The contract is specs/002-large-phase-remeasure/contracts/harness.md.
set -euo pipefail

refuse() {
  echo "oracle.sh: $*" >&2
  exit 2
}
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
write_n=no
[ "${1:-}" != --write-n ] || {
  write_n=yes
  shift
}
[ "$#" -eq 1 ] || refuse "usage: tests/eval/oracle.sh [--write-n] <fixture>"
fixture=$1
case $fixture in "" | */* | . | ..) refuse "unknown fixture '$fixture'" ;; esac
root=$(git -C "$here" rev-parse --show-toplevel)
rel=$(git -C "$here" rev-parse --show-prefix)fixtures/$fixture
for part in project heldout reference; do
  git -C "$root" cat-file -e "HEAD:$rel/$part" 2> /dev/null ||
    refuse "fixture '$fixture' has no committed $part/"
done
n_file=$here/fixtures/$fixture/heldout/N
if [ "$write_n" = no ]; then
  n=$(git -C "$root" show "HEAD:$rel/heldout/N" 2> /dev/null) ||
    refuse "fixture '$fixture' has no committed heldout/N: run with --write-n first"
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
extract() { git -C "$root" archive --format=tar "HEAD:$rel/$1" | tar -xf - -C "$2"; }
mkdir "$work/repo" "$work/repo/tests_heldout"
extract project "$work/repo"
extract reference "$work/repo"
extract heldout "$work/repo/tests_heldout"
rm -f "$work/repo/tests_heldout/N"

status=0
(cd "$work/repo" && uv run --locked pytest tests_heldout -q -p no:cacheprovider \
  --junitxml="$work/heldout.xml") > "$work/heldout.log" 2>&1 || status=$?
counts=$(python3 -c 'import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
suites = [root] if root.tag == "testsuite" else list(root)
n = lambda k: sum(int(s.get(k, 0)) for s in suites)
total = n("tests")
print(total - n("failures") - n("errors") - n("skipped"), total)' "$work/heldout.xml") || {
  cat "$work/heldout.log"
  echo "no junit report"
  exit 1
}
read -r passed total <<< "$counts"
all_passed=no
[ "$status" -eq 0 ] && [ "$passed" -eq "$total" ] && all_passed=yes
if [ "$write_n" = yes ]; then
  n=$total
  # A count from a failing run would make a wrong N look proven once committed.
  [ "$all_passed" = no ] || echo "$total" > "$n_file"
fi
echo "passed $passed/$total (N $n)"
[ "$all_passed" = yes ] && [ "$total" -eq "$n" ] && exit 0
cat "$work/heldout.log"
exit 1
