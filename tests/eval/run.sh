#!/usr/bin/env bash
# One arm of the eval (research.md R6): the fixture implemented headless by
# /speckit-implement without the preset, with it, or with it but no Agent tool,
# hermetic so the result is the preset's and anyone can rerun it.
#
# Usage:  tests/eval/run.sh <without|with|fallback> <out-dir>
# Exit:   0 counted (status ok); 1 not counted (status says why; rerun it, at
#         most twice); 2 refused (nothing written; fix it, do not retry)
#
# The contract is specs/001-story-workers/contracts/fragment.md, run.sh.
set -euo pipefail

refuse() {
  echo "run.sh: $*" >&2
  exit 2
}
# Bash builtins only until the tool check below has passed.
src=${BASH_SOURCE[0]}
case $src in */*) here=$(cd "${src%/*}" && pwd) ;; *) here=$(pwd) ;; esac

[ "$#" -eq 2 ] || refuse "usage: tests/eval/run.sh <without|with|fallback> <out-dir>"
arm=$1
case $arm in without | with | fallback) ;; *) refuse "unknown arm '$arm'" ;; esac
for tool in claude specify uv git python3 jq; do
  command -v "$tool" > /dev/null || refuse "missing $tool"
done
[ ! -e "$2" ] || refuse "$2 exists: every try gets a directory of its own"
root=$(git -C "$here" rev-parse --show-toplevel)
physical() { # <path>: its deepest existing ancestor resolved, symlinks and .. included
  local dir=$1 rest=
  case $dir in /*) ;; *) dir=$PWD/$dir ;; esac
  until [ -d "$dir" ]; do
    rest=/${dir##*/}$rest
    dir=${dir%/*}
    [ -n "$dir" ] || dir=/
  done
  echo "$(cd "$dir" && pwd -P)$rest"
}
target=$(physical "$2")
# A CLAUDE.md in any ancestor of the scratch repository loads into the run.
case $target/ in "$root"/*) refuse "$2 is inside $root: its CLAUDE.md would load into the run" ;; esac
# The `with` arms install HEAD's archive and versions.txt names HEAD: a change
# not in HEAD would be measured under a commit that does not contain it.
[ -z "$(git -C "$root" status --porcelain)" ] ||
  refuse "uncommitted changes in $root: commit them first"

mkdir -p "$2"
out=$(cd "$2" && pwd)
repo=$out/repo
# The fixture as committed: files git ignores (a stray .venv, tool caches) stay out.
mkdir "$repo"
(cd "$here" && git ls-files -z fixture | tar --null -T - -cf -) | tar -xf - -C "$repo" --strip-components 1
feature=$(jq -r .feature_directory "$repo/.specify/feature.json")

# Every step below runs in this environment: nothing of the caller's but what
# Claude Code's OAuth login and the tools need (R1 16), git kept from the
# user's config with a fixed identity (R1 15), and each step under a deadline
# that kills its whole process group (bounded.py).
allow=(HOME USER LOGNAME PATH TMPDIR LANG TERM)
speckit_python=${SPECKIT_PYTHON_EXECUTABLE:-$(uv tool dir)/specify-cli/bin/python}
isolation=(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@localhost
  GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@localhost)
clean() { # <seconds> <command> [args...]
  local seconds=$1 v pass=()
  shift
  for v in "${allow[@]}"; do
    [ -z "${!v+set}" ] || pass+=("$v=${!v}")
  done
  env -i "${pass[@]}" SPECKIT_PYTHON_EXECUTABLE="$speckit_python" "${isolation[@]}" \
    python3 "$here/bounded.py" "$seconds" "$@"
}

not_counted() {
  echo "not counted: $*" > "$out/status"
  echo "run.sh: not counted: $*" >&2
  exit 1
}
step() { # <name> <command> [args...]
  local name=$1
  shift
  clean 600 "$@" >> "$out/setup.log" 2>&1 || not_counted "setup: $name failed (setup.log)"
}

server=
www=$(mktemp -d)
trap '[ -z "$server" ] || kill "$server" 2> /dev/null; rm -rf "$www"' EXIT

cd "$repo"
step "git init" git init -q
step "specify init" specify init --here --force --integration claude
cmp -s "$here/fixture/.specify/feature.json" .specify/feature.json ||
  not_counted "setup: specify init changed .specify/feature.json"
if [ "$arm" != without ]; then
  # As a project installs it: the tag archive's shape, from HEAD, served from
  # localhost because the CLI takes plain HTTP from there only.
  git -C "$root" archive --format=zip --prefix="$(basename "$root")/" -o "$www/preset.zip" HEAD
  port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  python3 -m http.server "$port" --bind 127.0.0.1 --directory "$www" > /dev/null 2>&1 &
  server=$!
  for _ in $(seq 50); do
    curl -sf -o /dev/null "http://127.0.0.1:$port/preset.zip" && break
    sleep 0.1
  done
  step "preset add" specify preset add --from "http://127.0.0.1:$port/preset.zip"
fi
# What the arm installs is what it measures: checked before the costly run.
composed=no
if grep -q '^## Story workers' .claude/skills/speckit-implement/SKILL.md 2> /dev/null; then
  composed=yes
fi
[ "$composed" = "$([ "$arm" = without ] && echo no || echo yes)" ] ||
  not_counted "setup: preset not composed as the arm needs (Story workers section: $composed)"
step "git add" git add -A
step "setup commit" git commit -qm "fixture: setup"
setup=$(git rev-parse HEAD)

flags=(-p "/speckit-implement" --model claude-opus-5-5 --effort medium
  --setting-sources "project,local" --strict-mcp-config
  --allowedTools "Agent Bash Edit Write Read Glob Grep TodoWrite"
  --output-format stream-json --verbose)
[ "$arm" != fallback ] || flags+=(--disallowedTools Agent)
rc=0
clean 3600 claude "${flags[@]}" < /dev/null > "$out/stream.jsonl" 2> "$out/claude.stderr" || rc=$?

# Counting (R6): only whether this run is a measurement. What the feature does
# is judged on a counted run by SC-003, SC-005 and SC-007, so a rerun cannot
# hide a worker that misbehaved.
[ "$rc" -ne 124 ] || not_counted "deadline: 3600 s"
[ "$rc" -eq 0 ] || not_counted "exit $rc"
stream=$out/stream.jsonl
jq -s . "$stream" > /dev/null 2>&1 || not_counted "stream.jsonl is not JSON lines"
q() { jq -rs "$1" "$stream"; }
results=$(q '[.[] | select(.type == "result")] | length')
[ "$results" -eq 1 ] || not_counted "result events: $results"
[ "$(q '.[] | select(.type == "result") | .is_error')" = false ] || not_counted "is_error"
if [ "$arm" != with ]; then
  # In `with`, a denial is the feature misbehaving: SC-003 judges it.
  denials=$(q '.[] | select(.type == "result") | .permission_denials // [] | length')
  [ "$denials" -eq 0 ] || not_counted "permission denial: $denials"
fi
# The Agent tool's default subagent_type is general-purpose.
main_agent_calls='[.[] | select(.type == "assistant" and .parent_tool_use_id == null)
  | .message.content[]? | select(.type == "tool_use" and .name == "Agent")
  | {id} + .input + {subagent_type: (.input.subagent_type // "general-purpose")}]'
if [ "$arm" = without ]; then
  # The comparison's baseline needs the reviews the fixture asks for: a
  # `general-purpose` call per story that returned without an error (Explore
  # and the like are not reviews).
  stories=$(grep -c '^### User Story' "$repo/$feature/spec.md" || true)
  reviews=$(q "($main_agent_calls | map(select(.subagent_type == \"general-purpose\") | .id)) as \$ids
    | [.[] | select(.type == \"user\" and .parent_tool_use_id == null) | .message.content[]?
      | select(.type == \"tool_result\" and (.is_error // false | not)) | .tool_use_id
      | select(. as \$id | \$ids | index(\$id))] | unique | length")
  [ "$reviews" -ge "$stories" ] || not_counted "reviews: $reviews of $stories"
fi
init='first(.[] | select(.type == "system" and .subtype == "init"))'
style=$(q "$init | .output_style")
[ "$style" = default ] || not_counted "output style $style: the user's settings loaded"
plugins=$(q "[$init | .plugins[]? | select(.path != \"builtin\") | .name] | join(\",\")")
[ -z "$plugins" ] || not_counted "plugin outside Claude Code's built-in ones: $plugins"
mcp=$(q "$init | .mcp_servers | length")
[ "$mcp" -eq 0 ] || not_counted "mcp server: $mcp"

# A counted run: the project's own suite, then the held-out tests alone.
suite=0
clean 600 uv run pytest -q > "$out/suite.txt" 2>&1 || suite=$?
echo "exit: $suite" >> "$out/suite.txt"
cp -R "$here/heldout" "$repo/tests_heldout"
clean 600 uv run pytest tests_heldout -q --junitxml="$out/heldout.xml" > "$out/heldout.log" 2>&1 || true
{
  python3 -c 'import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
suites = [root] if root.tag == "testsuite" else list(root)
n = lambda k: sum(int(s.get(k, 0)) for s in suites)
total = n("tests")
print("passed %d/%d" % (total - n("failures") - n("errors") - n("skipped"), total))' \
    "$out/heldout.xml" || echo "passed 0/unknown: no junit report"
  cat "$out/heldout.log"
} > "$out/heldout.txt"

result='.[] | select(.type == "result")'
{
  # Cache tokens beside the cost: arms run back to back, so a later one may
  # read a prefix an earlier one wrote.
  q "$result | .modelUsage | to_entries[] | \"\(.key) \(.value.costUSD) cache_read \(.value.cacheReadInputTokens // 0) cache_creation \(.value.cacheCreationInputTokens // 0)\""
  q "[$result | .modelUsage[] | .costUSD] | \"sum \(add)\""
  q '[.[] | select(.type == "rate_limit_event") | .rate_limit_info.unifiedWindows.five_hour.utilization]
    | "five_hour \(first) \(last)"'
} > "$out/usage.txt"

semver() { grep -m1 -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' || echo unknown; }
{
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "commit: $(git -C "$root" rev-parse HEAD)"
  echo "claude: $(clean 600 claude --version | semver)"
  echo "specify: $(clean 600 specify version 2>&1 | semver)"
  echo "git: $(git --version | semver)"
  echo "uv: $(uv --version | semver)"
  echo "python: $(clean 600 uv run python --version 2>&1 | semver)"
  echo "pytest: $(clean 600 uv run pytest --version 2>&1 | semver)"
  echo "ruff: $(clean 600 uv run ruff --version 2>&1 | semver)"
  echo "main_model: claude-opus-5-5"
  echo "main_effort: medium"
  echo "environment: ${allow[*]} SPECKIT_PYTHON_EXECUTABLE"
  echo "git_isolation: ${isolation[*]}"
  echo "output_style: $style"
  echo "plugins: $(q "[$init | .plugins[]?.name] | join(\" \")")"
  echo "mcp_servers: $mcp"
  echo "skills: $(q "[$init | .skills[]?] | join(\" \")")"
} > "$out/versions.txt"

{
  q "$result | .modelUsage | keys[] | \"model \(.)\""
  echo "main claude-opus-5-5 effort medium"
  q "$main_agent_calls | group_by([.subagent_type, .model // \"-\", .effort // \"-\"])[]
    | \"agent \(.[0].subagent_type) \(.[0].model // \"-\") \(.[0].effort // \"-\") \(length)\""
} > "$out/models.txt"

clean 600 git log --reverse --format='commit %H%n%s' --name-only "$setup..HEAD" > "$out/commits.txt"
# The completion report, for SC-005's task ids and SC-003's line.
q "$result | .result" > "$out/report.txt"
echo ok > "$out/status"
