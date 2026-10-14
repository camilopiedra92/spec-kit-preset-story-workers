#!/usr/bin/env bash
# One arm of the eval (research.md R6): a fixture implemented headless by
# /speckit-implement without the preset, with it, or with it but no Agent tool,
# hermetic so the result is the preset's and anyone can rerun it.
#
# Usage:  tests/eval/run.sh [--baseline <run-dir>] [--state <name>] [--preset <ref>] <fixture> <without|with|fallback> <out-dir>
#         <fixture> is a directory under tests/eval/fixtures/ holding project/
#         (what the agent gets) and heldout/ (copied in after a counted run);
#         --baseline names a counted run whose versions this one must match;
#         --state lays fixtures/<fixture>/states/<name>/ over the project, after
#         the state its extends file names
# Exit:   0 counted (status ok); 1 not counted (status says why; rerun it, at
#         most twice); 2 refused (fix it, do not retry): before the out-dir
#         exists nothing is written; after, status says why
#
# The contract is specs/001-story-workers/contracts/fragment.md, run.sh, as
# specs/002-large-phase-remeasure/contracts/harness.md amends it.
set -euo pipefail

refuse() {
  echo "run.sh: $*" >&2
  exit 2
}
# Bash builtins only until the tool check below has passed.
src=${BASH_SOURCE[0]}
case $src in */*) here=$(cd "${src%/*}" && pwd) ;; *) here=$(pwd) ;; esac

usage="usage: tests/eval/run.sh [--baseline <run-dir>] [--state <name>] [--preset <ref>] <fixture> <without|with|fallback> <out-dir>"
baseline=
state=
preset=
while [ "$#" -gt 3 ]; do
  case $1 in
    --baseline)
      baseline=$2
      [ -f "$baseline/versions.txt" ] || refuse "baseline $baseline has no versions.txt"
      ;;
    # A committed state of the fixture laid over its project, as a feature
    # partly done (specs/003-resume-from-head, research R2).
    --state) state=$2 ;;
    # The preset as another ref archives it: the arm without the rule under
    # measurement, on the same fixture (specs/003-resume-from-head, research R3).
    --preset) preset=$2 ;;
    *) refuse "$usage" ;;
  esac
  shift 2
done
[ "$#" -eq 3 ] || refuse "$usage"
fixture=$1
arm=$2
# A plain name: no path can lead outside fixtures/.
case $fixture in "" | */* | . | ..) refuse "unknown fixture '$fixture'" ;; esac
case $arm in without | with | fallback) ;; *) refuse "unknown arm '$arm'" ;; esac
[ -z "$preset" ] || [ "$arm" != without ] || refuse "--preset applies to the with and fallback arms"
out_arg=$3
for tool in claude specify uv git python3 jq; do
  command -v "$tool" > /dev/null || refuse "missing $tool"
done
[ ! -e "$out_arg" ] || refuse "$out_arg exists: every try gets a directory of its own"
root=$(git -C "$here" rev-parse --show-toplevel)
fixture_dir=fixtures/$fixture
for part in project heldout; do
  [ -d "$here/$fixture_dir/$part" ] || refuse "fixture '$fixture' has no $part/"
done
fixture_rel=$(git -C "$here" rev-parse --show-prefix)$fixture_dir
preset_sha=$(git -C "$root" rev-parse --verify --quiet "${preset:-HEAD}^{commit}") ||
  refuse "unknown preset ref '$preset'"
# The state and the states it extends, base first: a state's extends file names
# the one it is laid over (specs/003-resume-from-head, research R2).
layers=()
name=$state
while [ -n "$name" ]; do
  case $name in */* | . | ..) refuse "unknown state '$name'" ;; esac
  git -C "$root" cat-file -e "HEAD:$fixture_rel/states/$name" 2> /dev/null ||
    refuse "fixture '$fixture' has no committed state '$name'"
  [ "${#layers[@]}" -lt 5 ] || refuse "state '$state' extends more than 5 deep"
  layers=("$name" ${layers[@]+"${layers[@]}"})
  # No extends file: the base of the chain.
  name=$({ git -C "$root" show "HEAD:$fixture_rel/states/$name/extends" 2> /dev/null || :; } |
    tr -d '[:space:]')
done
lay() { # <committed|uncommitted>: each layer's part, as committed, base first
  local layer
  for layer in ${layers[@]+"${layers[@]}"}; do
    git -C "$root" cat-file -e "HEAD:$fixture_rel/states/$layer/$1" 2> /dev/null || continue
    git -C "$root" archive --format=tar "HEAD:$fixture_rel/states/$layer/$1" | tar -xf - -C "$repo"
  done
}
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
target=$(physical "$out_arg")
# A CLAUDE.md in any ancestor of the scratch repository loads into the run.
case $target/ in "$root"/*) refuse "$out_arg is inside $root: its CLAUDE.md would load into the run" ;; esac
# The `with` arms install HEAD's archive and versions.txt names HEAD: a change
# not in HEAD would be measured under a commit that does not contain it.
[ -z "$(git -C "$root" status --porcelain)" ] ||
  refuse "uncommitted changes in $root: commit them first"

mkdir -p "$out_arg"
out=$(cd "$out_arg" && pwd)
repo=$out/repo
# The fixture as committed: files git ignores (a stray .venv, tool caches) stay out.
mkdir "$repo"
(cd "$here/$fixture_dir" && git ls-files -z project | tar --null -T - -cf -) |
  tar -xf - -C "$repo" --strip-components 1
# committed/ as committed in this repository, laid over the project before the
# setup commit; uncommitted/ comes after it (below).
lay committed
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
  # The auto-updater off: a Claude Code update mid-eval would split the runs
  # across versions (research R9).
  env -i "${pass[@]}" SPECKIT_PYTHON_EXECUTABLE="$speckit_python" "${isolation[@]}" \
    DISABLE_AUTOUPDATER=1 python3 "$here/bounded.py" "$seconds" "$@"
}

refused() { # once <out-dir> exists: the reason in status, exit 2
  echo "refused: $*" > "$out/status"
  echo "run.sh: refused: $*" >&2
  exit 2
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
cmp -s "$here/$fixture_dir/project/.specify/feature.json" .specify/feature.json ||
  not_counted "setup: specify init changed .specify/feature.json"
if [ "$arm" != without ]; then
  # As a project installs it: the tag archive's shape, from HEAD, served from
  # localhost because the CLI takes plain HTTP from there only.
  git -C "$root" archive --format=zip --prefix="$(basename "$root")/" -o "$www/preset.zip" "$preset_sha"
  port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  python3 -m http.server "$port" --bind 127.0.0.1 --directory "$www" > /dev/null 2>&1 &
  server=$!
  # Killed by the EXIT trap; disowned so bash does not report it as a job.
  disown "$server"
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
# A state's uncommitted/: changes the agent finds in the working tree, as a
# user leaves them (specs/003-resume-from-head, research R2).
lay uncommitted
measured=$(git -C "$root" rev-parse HEAD)

# The versions known before the agent starts, none read from the scratch
# repository; with a baseline, a difference is refused before anything is spent.
semver() { grep -m1 -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' || echo unknown; }
{
  echo "commit: $measured"
  echo "claude: $(clean 600 claude --version | semver)"
  echo "specify: $(clean 600 specify version 2>&1 | semver)"
  echo "git: $(git --version | semver)"
  echo "uv: $(uv --version | semver)"
  echo "main_model: claude-opus-5-5"
  echo "main_effort: medium"
  echo "environment: ${allow[*]} SPECKIT_PYTHON_EXECUTABLE"
  echo "git_isolation: ${isolation[*]}"
  echo "fixture: $fixture"
  echo "arm: $arm"
  echo "autoupdater: disabled"
  echo "state: ${state:--}"
  echo "preset: ${preset:-HEAD} $preset_sha"
} > "$out/versions.txt"
differing() { # <key>...: those whose line differs between this run and the baseline
  local key
  for key in "$@"; do
    [ "$(grep -m1 "^$key: " "$out/versions.txt")" = "$(grep -m1 "^$key: " "$baseline/versions.txt")" ] ||
      printf '%s ' "$key"
  done
}
pre_run=(commit claude specify git uv main_model main_effort environment git_isolation fixture autoupdater state preset)
if [ -n "$baseline" ]; then
  keys=$(differing "${pre_run[@]}")
  [ -z "$keys" ] || refused "versions differ from the baseline: ${keys% }"
fi

flags=(-p "/speckit-implement" --model claude-opus-5-5 --effort medium
  --setting-sources "project,local" --strict-mcp-config
  --allowedTools "Agent Bash Edit Write Read Glob Grep TodoWrite"
  --output-format stream-json --verbose)
[ "$arm" != fallback ] || flags+=(--disallowedTools Agent)
rc=0
clean 3600 claude "${flags[@]}" < /dev/null > "$out/stream.jsonl" 2> "$out/claude.stderr" || rc=$?

# The run's transcripts, whatever its exit, while Claude Code still keeps them:
# usage.py attributes a counted run from them, and a killed run is priced from
# them for the eval's spend (research R3).
session=$(jq -r 'select(.type == "system" and .subtype == "init") | .session_id // empty' \
  "$out/stream.jsonl" 2> /dev/null | head -n 1 || true)
if [ -n "$session" ]; then
  for found in "$HOME"/.claude/projects/*/"$session".jsonl; do
    [ -f "$found" ] || continue
    mkdir -p "$out/transcripts"
    cp "$found" "$out/transcripts/"
    [ ! -d "${found%.jsonl}/subagents" ] || cp -R "${found%.jsonl}/subagents" "$out/transcripts/"
    break
  done
fi

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
{
  echo "output_style: $style"
  echo "plugins: $(q "[$init | .plugins[]?.name] | join(\" \")")"
  echo "mcp_servers: $mcp"
  echo "skills: $(q "[$init | .skills[]?] | join(\" \")")"
} >> "$out/versions.txt"
if [ -n "$baseline" ]; then
  keys=$(differing output_style plugins mcp_servers skills)
  [ -z "$keys" ] || not_counted "versions differ from the baseline: ${keys% }"
fi
# The usage, reconciled with what Claude Code reported and attributed: a run
# without it is no measurement (spec Clarifications).
attributed=0
python3 "$here/usage.py" "$out" > "$out/usage.log" 2>&1 || attributed=$?
last=$(tail -n 1 "$out/usage.log")
# Only usage.py's own verdict makes a run not counted; any other exit, Python's
# exit 1 on an exception before main() included, is the harness's fault.
case $attributed:$last in
  0:*) ;;
  1:unreconciled:*) not_counted "$last" ;;
  *) refused "harness fault: $last (usage.log)" ;;
esac

# A counted run: the project's own suite, then the held-out tests alone.
suite=0
clean 600 uv run pytest -q > "$out/suite.txt" 2>&1 || suite=$?
echo "exit: $suite" >> "$out/suite.txt"
# The held-out tests as committed at the measured commit: the tree was checked
# clean before the run, but a run lasts up to an hour and the fixture may move.
mkdir "$repo/tests_heldout"
git -C "$root" archive --format=tar "$measured:$(git -C "$here" rev-parse --show-prefix)$fixture_dir/heldout" |
  tar -xf - -C "$repo/tests_heldout"
rm -f "$repo/tests_heldout/N"
clean 600 uv run pytest tests_heldout -q --junitxml="$out/heldout.xml" > "$out/heldout.log" 2>&1 || true
{
  python3 -c 'import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
suites = [root] if root.tag == "testsuite" else list(root)
n = lambda k: sum(int(s.get(k, 0)) for s in suites)
total = n("tests")
print("passed %d/%d" % (total - n("failures") - n("errors") - n("skipped"), total))' \
    "$out/heldout.xml" || echo "passed 0/0: no junit report"
  cat "$out/heldout.log"
} > "$out/heldout.txt"

result='.[] | select(.type == "result")'
{
  echo "python: $(clean 600 uv run python --version 2>&1 | semver)"
  echo "pytest: $(clean 600 uv run pytest --version 2>&1 | semver)"
  echo "ruff: $(clean 600 uv run ruff --version 2>&1 | semver)"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$out/versions.txt"

{
  q "$result | .modelUsage | keys[] | \"model \(.)\""
  echo "main claude-opus-5-5 effort medium"
  q "$main_agent_calls | group_by([.subagent_type, .model // \"-\", .effort // \"-\"])[]
    | \"agent \(.[0].subagent_type) \(.[0].model // \"-\") \(.[0].effort // \"-\") \(length)\""
} > "$out/models.txt"

# --no-renames: a moved file shows its old path too.
clean 600 git log --reverse --no-renames --format='commit %H%n%s' --name-only "$setup..HEAD" > "$out/commits.txt"
# The completion report, for SC-005's task ids and SC-003's line.
q "$result | .result" > "$out/report.txt"
echo ok > "$out/status"
