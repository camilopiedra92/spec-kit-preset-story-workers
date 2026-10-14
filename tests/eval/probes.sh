#!/usr/bin/env bash
# Reruns the observations of research.md R1 the design rests on, headless and
# hermetic as the eval runs, so a Claude Code release that breaks one is a red
# probe rather than a silent change in the eval. Spends a little usage.
#
# Usage:  tests/eval/probes.sh [out-dir]   (out-dir keeps every probe's repo
#                                           and stream; a temporary one if none)
# Exit:   0 every probe ok; 1 one or more FAIL; 2 a missing tool
#
# R1 6, 12 and 16 are checked on every eval run instead (run.sh); 2 is covered
# by 9; 13 and 14 are recorded, not relied on.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for tool in claude git python3 jq; do
  command -v "$tool" > /dev/null || {
    echo "probes.sh: missing $tool" >&2
    exit 2
  }
done
if [ "$#" -ge 1 ]; then
  mkdir -p "$1"
  out=$(cd "$1" && pwd)
else
  out=$(mktemp -d)
fi

allow=(HOME USER LOGNAME PATH TMPDIR LANG TERM)
isolation=(GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@localhost
  GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@localhost)
EVAL_TOOLS="Agent Bash Edit Write Read Glob Grep TodoWrite"

# claude_in <repo> <stream> [VAR=value...] -- [claude flags...] <prompt>: headless,
# in the eval's clean environment plus any VAR=value given, under a deadline. The
# prompt goes right after -p: --allowedTools and --disallowedTools take every
# argument after them, a trailing prompt included.
claude_in() {
  local repo=$1 stream=$2 v prompt pass=() extra=()
  shift 2
  while [ "$1" != -- ]; do
    extra+=("$1")
    shift
  done
  shift
  prompt=${!#}
  set -- "${@:1:$#-1}"
  for v in "${allow[@]}"; do
    [ -z "${!v+set}" ] || pass+=("$v=${!v}")
  done
  # The auto-updater off, as in run.sh: the probes and the runs must be one
  # Claude Code version (research R9).
  (cd "$repo" && env -i "${pass[@]}" "${isolation[@]}" DISABLE_AUTOUPDATER=1 \
    ${extra[@]+"${extra[@]}"} python3 "$here/bounded.py" 1200 claude -p "$prompt" --model claude-opus-5-5 --effort medium \
    --setting-sources "project,local" --strict-mcp-config --output-format stream-json --verbose \
    "$@" > "$stream" 2> "$stream.stderr") || true
}

scratch() { # <name>: a fresh git repository for one probe
  local repo=$out/$1
  mkdir -p "$repo"
  git -C "$repo" init -q
  echo "$repo"
}

failed=0
oks=0
fails=0
expect() { # <probe> <what was seen> <command...>: ok when the command succeeds
  local probe=$1 seen=$2
  shift 2
  if "$@"; then
    echo "ok   $probe"
    oks=$((oks + 1))
  else
    echo "FAIL $probe: $seen"
    fails=$((fails + 1))
    failed=1
  fi
}
has() { jq -es "$2" "$1" > /dev/null 2>&1; } # <stream> <jq test over all events>

usage_models() { jq -rs '[.[] | select(.type == "result") | .modelUsage | keys[]] | join(" ")' "$1"; }
thinking() { # <stream> <model substring>
  jq -rs --arg m "$2" '[.[] | select(.type == "result") | .modelUsage | to_entries[]
    | select(.key | contains($m)) | .value.thinkingTokens] | add // 0' "$1"
}
agent_replies() { # every tool_result the main session received, as text
  jq -rs '[.[] | select(.type == "user" and .parent_tool_use_id == null) | .message.content[]?
    | select(.type == "tool_result") | .content | tostring] | join("\n")' "$1"
}

echo "claude $(DISABLE_AUTOUPDATER=1 claude --version)"

# R1 1: a call's model decides the subagent's; its events carry the call's id.
repo=$(scratch r1-1)
s=$out/r1-1.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" \
  'Start one general-purpose subagent with model "sonnet" and run_in_background false that replies only "A", without tools. Then answer with its reply.'
expect "R1 1: model on the call, subagent events by parent id" "models: $(usage_models "$s")" \
  has "$s" '([.[] | select(.type == "result") | .modelUsage | keys[]] | any(contains("sonnet")) and any(contains("opus")))
    and ([.[] | .message.content[]? | select(.type == "tool_use" and .name == "Agent") | .id] as $ids
      | any(.[]; .parent_tool_use_id as $p | $p != null and ($ids | index($p))))'

# R1 3: the project's CLAUDE.md reaches the subagent.
repo=$(scratch r1-3)
echo "PROBE-MARKER-7f3a: this line identifies the project's instructions." > "$repo/CLAUDE.md"
s=$out/r1-3.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" \
  'Start one general-purpose subagent with model "sonnet". Tell it: "Without using any tool, reply with the line of your instructions that starts with PROBE-MARKER." Then answer with its reply verbatim.'
expect "R1 3: project CLAUDE.md reaches the subagent" "subagent replied: $(agent_replies "$s" | head -c 200)" \
  grep -q PROBE-MARKER-7f3a <(agent_replies "$s")

# R1 4: the call's model wins over CLAUDE_CODE_SUBAGENT_MODEL, for both families.
for family in sonnet opus; do
  repo=$(scratch "r1-4-$family")
  s=$out/r1-4-$family.jsonl
  claude_in "$repo" "$s" CLAUDE_CODE_SUBAGENT_MODEL=haiku -- --allowedTools "$EVAL_TOOLS" \
    "Start one general-purpose subagent with model \"$family\" that replies only \"A\", without tools. Then answer with its reply."
  expect "R1 4: model \"$family\" on the call beats CLAUDE_CODE_SUBAGENT_MODEL=haiku" \
    "models: $(usage_models "$s")" \
    has "$s" "[.[] | select(.type == \"result\") | .modelUsage | keys[]] as \$k
      | (\$k | any(contains(\"haiku\")) | not) and ([.[] | select(.type == \"user\") | .message.content[]?
      | select(.type == \"tool_result\")] | length > 0)
      and (\"$family\" != \"sonnet\" or (\$k | any(contains(\"sonnet\"))))"
done

# R1 5 and 8: the call's effort applies, with the built-in agent and with a
# project's own general-purpose agent.
COUNTING='Without using any tool, count how many times the letter e appears in this sentence and reply with the number only: "Every eleventh evening the seventeen elegant elephants entered the deserted temple, reverently remembering their seemingly endless trek between the green meadows."'
effort_probe() { # <name> <label> [setup command]
  local name=$1 label=$2 low high e
  for e in low max; do
    repo=$(scratch "$name-$e")
    [ "$#" -lt 3 ] || "$3" "$repo"
    claude_in "$repo" "$out/$name-$e.jsonl" -- --allowedTools "$EVAL_TOOLS" \
      "Start one general-purpose subagent with model \"sonnet\", effort \"$e\" and run_in_background false. Tell it: \"$COUNTING\" Then answer with its reply."
  done
  low=$(thinking "$out/$name-low.jsonl" sonnet)
  high=$(thinking "$out/$name-max.jsonl" sonnet)
  expect "$label" "Sonnet thinking tokens: low $low, max $high" [ "$high" -gt "$low" ]
}
own_agent() { # a project general-purpose agent with its own model and a marker
  mkdir -p "$1/.claude/agents"
  printf -- '---\nname: general-purpose\ndescription: General-purpose agent for any task.\nmodel: haiku\n---\nAlways include the word PROBE-AGENT-91c in every reply.\n' \
    > "$1/.claude/agents/general-purpose.md"
}
effort_probe r1-5 "R1 5: effort on the call applies"

# R1 7: a project's general-purpose agent supplies the prompt; the call's model still decides.
repo=$(scratch r1-7)
own_agent "$repo"
s=$out/r1-7.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" \
  'Start one general-purpose subagent with model "sonnet". Tell it: "Without using any tool, reply with the word your instructions tell you to include." Then answer with its reply.'
expect "R1 7: project agent's prompt, call's model" \
  "models: $(usage_models "$s"); replied: $(agent_replies "$s" | head -c 160)" \
  has "$s" '([.[] | select(.type == "result") | .modelUsage | keys[]] | any(contains("sonnet")) and (any(contains("haiku")) | not))
    and ([.[] | select(.type == "result") | .is_error] == [false])
    and ([.[] | select(.type == "user") | .message.content[]? | select(.type == "tool_result") | .content | tostring]
      | any(contains("PROBE-AGENT-91c")))'

effort_probe r1-8 "R1 8: effort on the call applies with a project agent" own_agent

# R1 9: a project PreToolUse hook blocks a subagent's write and counts as a denial.
repo=$(scratch r1-9)
mkdir -p "$repo/.claude"
cat > "$repo/.claude/settings.json" << 'EOF'
{"hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [{"type": "command",
  "command": "echo 'PROBE-HOOK: writes are blocked here' >&2; exit 2"}]}]}}
EOF
s=$out/r1-9.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" \
  'Start one general-purpose subagent with model "sonnet". Tell it: "Use the Write tool to create blocked.txt containing x, then report what happened." Then answer with its report.'
expect "R1 9: a hook blocks the subagent's write, counted as a denial" \
  "blocked.txt $([ -e "$repo/blocked.txt" ] && echo exists || echo absent); denials $(jq -rs '[.[] | select(.type == "result") | .permission_denials | length] | add' "$s")" \
  has "$s" '[.[] | select(.type == "result") | .permission_denials | length] | add >= 1'
expect "R1 9: the blocked file was not written" "blocked.txt exists" [ ! -e "$repo/blocked.txt" ]

# R1 10: Stop fires once, at the end of the main session's turn, not per subagent.
repo=$(scratch r1-10)
mkdir -p "$repo/.claude"
cat > "$repo/.claude/settings.json" << 'EOF'
{"hooks": {
  "Stop": [{"hooks": [{"type": "command", "command": "echo stop >> \"$CLAUDE_PROJECT_DIR/hooks.log\""}]}],
  "SubagentStop": [{"hooks": [{"type": "command", "command": "echo substop >> \"$CLAUDE_PROJECT_DIR/hooks.log\""}]}]}}
EOF
claude_in "$repo" "$out/r1-10.jsonl" -- --allowedTools "$EVAL_TOOLS" \
  'Start a general-purpose subagent with model "sonnet" that replies only "A", without tools. After its reply, start a second one, model "sonnet", that replies only "B". Then answer with both replies.'
log=$( (tr '\n' ' ' < "$repo/hooks.log") 2> /dev/null || true)
expect "R1 10: SubagentStop per subagent, Stop once at the end" "hooks.log: $log" [ "$log" = "substop substop stop " ]

# R1 11: --disallowedTools Agent removes the Agent tool.
repo=$(scratch r1-11)
s=$out/r1-11.jsonl
claude_in "$repo" "$s" -- --allowedTools Agent --disallowedTools Agent \
  'If you have an Agent tool, start a general-purpose subagent that replies "A". If you do not, answer exactly: NO-AGENT-TOOL.'
expect "R1 11: no Agent tool under --disallowedTools Agent" \
  "spawned $(jq -rs '[.[] | select(.type == "result") | .subagent_stats.spawned // 0] | add' "$s")" \
  has "$s" '([.[] | select(.type == "result") | .subagent_stats.spawned // 0] | add == 0)
    and ([.[] | .message.content[]? | select(.type == "tool_use" and .name == "Agent")] | length == 0)'

# R1 15: core /speckit-implement completes headless, hermetic, git isolated,
# with the eval's tool list.
repo=$(scratch r1-15)
(cd "$repo" && env -i "PATH=$PATH" "HOME=$HOME" "${isolation[@]}" \
  python3 "$here/bounded.py" 600 specify init --here --force --integration claude > "$out/r1-15-init.log" 2>&1) || true
mkdir -p "$repo/specs/001-add" "$repo/.specify"
echo '{"feature_directory": "specs/001-add"}' > "$repo/.specify/feature.json"
cat > "$repo/specs/001-add/spec.md" << 'EOF'
# Feature Specification: Add

### User Story 1 - Add two numbers (Priority: P1)

1. **Given** 2 and 3, **When** added, **Then** 5.
EOF
cat > "$repo/specs/001-add/plan.md" << 'EOF'
# Implementation Plan: Add

## Technical Context

**Language/Version**: Python 3 standard library only

**Testing**: `python3 -m unittest`
EOF
cat > "$repo/specs/001-add/tasks.md" << 'EOF'
# Tasks: Add

## Phase 1: User Story 1

- [ ] T001 Create `add.py` with `def add(a: int, b: int) -> int` returning their sum, and `test_add.py` checking `add(2, 3) == 5` with unittest
EOF
(cd "$repo" && env -i "PATH=$PATH" "HOME=$HOME" "${isolation[@]}" sh -c 'git add -A && git commit -qm setup') > /dev/null 2>&1 || true
s=$out/r1-15.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" "/speckit-implement"
unit=$( (cd "$repo" && python3 -m unittest test_add > /dev/null 2>&1) && echo pass || echo fail)
expect "R1 15: core implement completes headless" \
  "result $(jq -cs '[.[] | select(.type == "result") | {is_error, d: (.permission_denials | length)}]' "$s"); task $(grep -c '\[[xX]\] T001' "$repo/specs/001-add/tasks.md" || true); test $unit" \
  sh -c "[ \"$unit\" = pass ] && grep -q '\[[xX]\] T001' '$repo/specs/001-add/tasks.md' && jq -es '[.[] | select(.type == \"result\")] | length == 1 and .[0].is_error == false and (.[0].permission_denials | length) == 0' '$s' > /dev/null"

# R1 17: a foreground worker returns after its own events; the eval's tool list
# lets it write and commit with no denial; the next call comes after.
repo=$(scratch r1-17)
s=$out/r1-17.jsonl
claude_in "$repo" "$s" -- --allowedTools "$EVAL_TOOLS" \
  'Start a general-purpose subagent with model "sonnet" and run_in_background false. Tell it: "Use the Write tool to create a.txt containing A, then run git add a.txt and git commit -m probe-a." After it has replied, start a second one, model "sonnet", run_in_background false, that replies only "B" without tools. Then answer with both replies.'
expect "R1 17: foreground calls in order, each result after its own events" "see $s" \
  has "$s" '[to_entries[] | {i: .key, e: .value}] as $ev
    | [$ev[] | .i as $i | .e.message.content[]? | select(.type == "tool_use" and .name == "Agent") | {id, i: $i}] as $calls
    | ($calls | length) == 2
    and ([$calls[] | .id as $id | [$ev[] | select(.e.type == "user") | .i as $i | .e.message.content[]?
      | select(.type == "tool_result" and .tool_use_id == $id) | $i][0]] as $results
      | ($results[0] < $calls[1].i)
      and all(range(0; 2) as $n | [$ev[] | select(.e.parent_tool_use_id == $calls[$n].id) | .i] | length > 0 and max < $results[$n]))'
expect "R1 17: the worker wrote and committed with no denial" \
  "a.txt $([ -e "$repo/a.txt" ] && echo exists || echo absent); log $(git -C "$repo" log --format=%s 2> /dev/null | tr '\n' ' ')" \
  sh -c "[ -e '$repo/a.txt' ] && git -C '$repo' log --format=%s | grep -qx probe-a && jq -es '[.[] | select(.type == \"result\") | .permission_denials | length] | add == 0' '$s' > /dev/null"

# The closing summary: runs.sh and compare.py require it, so a file cut short fails.
echo "probes: $oks ok, $fails FAIL"
echo "streams and repositories: $out"
exit "$failed"
