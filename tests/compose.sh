#!/usr/bin/env bash
# Installs this preset into a scratch Spec Kit project with the real CLI and
# checks what it does to the skill it appends to. The CLI version is whatever
# `specify` is on PATH: CI runs it pinned and against the latest release, which
# is how an upstream change to the core skill shows up here before it shows up
# in a project.
#
# Usage:  tests/compose.sh        from anywhere in the repository
set -euo pipefail

PRESET="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work=$(mktemp -d)
server=
trap '[ -n "$server" ] && kill "$server" 2> /dev/null; rm -rf "$work"' EXIT
# Quiet on success, the whole output on failure: the CLI reports through a
# rich console on stdout, so silencing it blindly hides why CI failed.
quiet() {
  "$@" > "$work/last.log" 2>&1 || {
    echo "FAIL: $*"
    cat "$work/last.log"
    exit 1
  }
}
fail=0
problem() {
  echo "FAIL: $*"
  fail=1
}

# The specify CLI's own environment ships PyYAML; the system python3 may not.
PY="${SPECKIT_PYTHON_EXECUTABLE:-$(uv tool dir)/specify-cli/bin/python}"
description() {
  "$PY" -c 'import sys, yaml
text = open(sys.argv[1], encoding="utf-8").read()
print(yaml.safe_load(text.split("---")[1])["description"])' "$1"
}
# The commands come from preset.yml, so a command added there is checked
# without touching this script: one "speckit.x<TAB>commands/x.md" per line.
# Manifest and fragments are read from HEAD, like the archive installed below.
git -C "$PRESET" show HEAD:preset.yml > "$work/preset.yml" 2> "$work/last.log" || {
  echo "FAIL: no preset.yml at HEAD"
  exit 1
}
"$PY" -c 'import sys, yaml
m = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
for t in m["provides"]["templates"]:
    if t["type"] != "command" or t.get("strategy") != "append":
        sys.exit("compose.sh checks appended commands only: " + t["name"])
    print(t["name"] + "\t" + t["file"])' "$work/preset.yml" > "$work/commands.tsv"

# Installed the way a project installs it: GitHub's tag archive is a zip of the
# committed tree under one top-level directory, minus export-ignore paths, and
# `--from` downloads it. git archive builds the same shape from HEAD, and the
# CLI accepts plain HTTP from localhost only, so a local server stands in for
# GitHub. Uncommitted changes are not in HEAD and so are not tested.
mkdir "$work/www"
prefix="$(basename "$PRESET")/"
quiet git -C "$PRESET" archive --format=zip --prefix="$prefix" \
  -o "$work/www/preset.zip" HEAD

# Whatever the archive carries lands in every project that installs it
# (constitution V): this repository's development files must stay out.
"$PY" -c 'import sys, zipfile
for n in zipfile.ZipFile(sys.argv[1]).namelist():
    print(n[len(sys.argv[2]):])' "$work/www/preset.zip" "$prefix" > "$work/archive.txt"
for dev in .specify/ .claude/ specs/ tests/ docs/ .github/ CLAUDE.md .gitignore \
  pyproject.toml uv.lock; do
  # A path itself, or anything under it when it names a directory.
  awk -v p="$dev" '$0 == p || (p ~ /\/$/ && index($0, p) == 1) { found = 1 } END { exit !found }' \
    "$work/archive.txt" && problem "the archive carries $dev; mark it export-ignore"
done

port=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
python3 -m http.server "$port" --bind 127.0.0.1 --directory "$work/www" > /dev/null 2>&1 &
server=$!
disown "$server"
for _ in $(seq 50); do
  curl -sf -o /dev/null "http://127.0.0.1:$port/preset.zip" && break
  sleep 0.1
done

cd "$work"
quiet git init -q
# The skills are what is under test, not Claude Code, which a runner lacks:
# without this, init stops at "claude not found".
quiet specify init --here --force --integration claude --ignore-agent-tools
skill_of() { echo ".claude/skills/${1//./-}/SKILL.md"; }
mkdir core
while IFS=$'\t' read -r name _; do
  cp "$(skill_of "$name")" "core/$name.md"
done < commands.tsv

# The fragment narrows these core rules and points the worker at these core
# steps by name; tests/core-anchors.sh names any upstream dropped or reworded.
"$PRESET/tests/core-anchors.sh" core/speckit.implement.md || fail=1
# SC-004 (specs/002): each anchor removed from a copy of core turns the check
# red, naming it, so a check that stopped looking for one cannot pass unseen.
while IFS= read -r anchor; do
  "$PY" -c 'import sys
text = " ".join(open(sys.argv[1], encoding="utf-8").read().split())
open(sys.argv[3], "w", encoding="utf-8").write(text.replace(sys.argv[2], ""))' \
    core/speckit.implement.md "$anchor" core-cut.md
  if said_missing=$("$PRESET/tests/core-anchors.sh" core-cut.md); then
    problem "core-anchors.sh passed a core without '$anchor'"
  elif ! grep -qF -- "'$anchor'" <<< "$said_missing"; then
    problem "core-anchors.sh did not name the removed '$anchor'"
  fi
done < <("$PRESET/tests/core-anchors.sh" --list)
[ "$fail" -ne 0 ] ||
  echo "ok: SC-004, $("$PRESET/tests/core-anchors.sh" --list | wc -l | tr -d ' ') anchors each turned the check red"

quiet specify preset add --from "http://127.0.0.1:$port/preset.zip"

while IFS=$'\t' read -r name file; do
  skill=$(skill_of "$name")
  fragment="fragment.md"
  git -C "$PRESET" show "HEAD:$file" > "$fragment"
  # An empty fragment would pass the tail comparison below.
  grep -q '[^[:space:]]' "$fragment" || problem "$file is empty"
  # Appended: the whole core body survives verbatim, then the fragment closes
  # the file. Not compared line for line from the top: on composing, the CLI
  # re-serializes the frontmatter and adds a title heading (1.1.0).
  "$PY" -c 'import sys
body = lambda p: open(p, encoding="utf-8").read().split("---", 2)[2].strip()
sys.exit(body(sys.argv[1]) not in body(sys.argv[2]))' "core/$name.md" "$skill" ||
    problem "$name lost or changed the core body"
  # Trailing whitespace aside, which the CLI trims when it composes.
  "$PY" -c 'import sys
read = lambda p: open(p, encoding="utf-8").read().rstrip()
sys.exit(not read(sys.argv[2]).endswith(read(sys.argv[1])))' "$fragment" "$skill" ||
    problem "$name does not end with the fragment"
  # The description is what Claude reads to decide when to invoke the skill;
  # a fragment with frontmatter replaces it. Compared as parsed YAML, because
  # the CLI re-serializes the frontmatter whenever it composes a skill.
  [ "$(description "$skill")" = "$(description "core/$name.md")" ] ||
    problem "$name description changed: $(description "$skill")"
done < commands.tsv

# The rules of contracts/fragment.md, by the phrases that state them. Matched
# in the fragment, not the whole composed skill: core carries the narrowed
# rules' own text, which would satisfy a match on the composed file. The check
# above has already tied the composed skill's tail to this fragment.
git -C "$PRESET" show HEAD:commands/speckit.implement.md > implement.md 2> /dev/null || : > implement.md
said=$(tr -s '[:space:]' ' ' < implement.md)
phrases=(
  'subagent_type: "general-purpose"'
  'model: "sonnet"'
  'effort: "medium"'
  'run_in_background: false'
  'hand each phase to a worker'
  "opens with the phase's heading"
  "follow core's"
  'commits each task'
  'marks a task [X] only after'
  'at most two fix hand-offs'
  "carry out the phase's remaining items in this session"
  'tasks: mark phase'
  'tasks: add found tasks'
  "with \`model\` set to this session's model family"
  'carry out the remaining tasks in this session'
  'Carried out in this session:'
  # Each narrowed core rule, named by its exact text (constitution I).
  'For completed tasks, make sure to mark the task off as [X]'
  'parallel tasks [P] can run together'
  'Halt execution if any non-parallel task fails'
)
for phrase in "${phrases[@]}"; do
  grep -qF -- "$phrase" <<< "$said" || problem "the fragment does not say '$phrase'"
done

specify version > version.txt 2>&1 || true
[ "$fail" -eq 0 ] && echo "ok: composes on specify $(grep -m1 -oE '[0-9]+\.[0-9]+\.[0-9]+' version.txt)"
exit "$fail"
