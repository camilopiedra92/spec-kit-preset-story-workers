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
# An allowlist: a new development file that is not export-ignored fails here
# rather than reaching every project.
while IFS= read -r path; do
  case $path in
    commands/*/*) problem "the archive carries $path; commands/ holds one level of fragments" ;;
    "" | preset.yml | README.md | CHANGELOG.md | LICENSE | commands/ | commands/*.md) ;;
    *) problem "the archive carries $path; mark it export-ignore or allow it here" ;;
  esac
done < "$work/archive.txt"

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
  # Where a run starts (0.2.0, specs/003-resume-from-head): core's marks
  # decide; nothing is reconstructed from history; changes made before the run
  # are the user's. One phrase per clause. A phrase proves the clause is there,
  # not that no qualifier ("except ...") was added beside it: that is the
  # reviewer's to read.
  '`[X]` or `[x]`'
  'read from the file as core reads it'
  'Where a run starts is never read from commit messages'
  'skips every phase whose tasks are all marked, wherever it falls'
  'It starts at the first phase with an unmarked task, at Phase 1 when none is marked'
  'When every task is marked, start no worker, commit nothing'
  "Each phase's baseline is taken as Verification says"
  "Before a phase's first worker, record HEAD"
  "the phase's unmarked tasks"
  'may already be done, in whole or in part'
  'check each against the code and `git log`'
  'complete only what is missing'
  'tasks found already done'
  'the static checks and its reading of the commit or file the worker cites'
  'staging only the files it changed, never `git add -A` or `-a`'
  "(Phase 1's worker only)"
  'neither asks about them nor stops for them'
  'the commits made since the recorded HEAD'
  # A clean tree outside the feature directory (the third review's design).
  'commits what Project Setup Verification changes in a commit of its own'
  'never edits, stages, commits or reverts a file in the feature directory'
  'run before its own suite and static-check runs, lists nothing outside the feature directory'
  'goes back to it as a finding'
  'Outside the items this session carries out, your only edits'
  'When it lists a path outside the feature directory'
  'carry out the run in this session as core does'
  'They are not a finding'
  'No worker edits, stages, commits or reverts a file there'
  'carry `tasks.md` as it stands, its earlier edits included'
  'A task that changes a file in the feature directory is carried out in this session as core does'
  '`tasks: carried out in this session`'
  'uncommitted changes stay as they are'
  'Its files in the feature directory are left uncommitted, as core leaves them'
  'What this session changes outside the feature directory while carrying out'
  'leaves a task that needs one unfinished, saying so'
  '`git status --porcelain --untracked-files=all`, run before its own suite'
  'an unfinished task that changes the feature directory, which this session carries out'
  'any file the suite or the static checks generate that git does not ignore'
  "Before the first worker and before any of the run's own suite or static-check runs"
  'it commits as soon as it has carried them out, before any later Verification or worker'
  "Commits that core's extension hooks make are core's"
  'When a phase went to a worker, the completion report carries the line'
  'name those paths in the completion report'
  'say so in the completion report in place of the line below'
  'uncommitted changes outside the feature directory'
  'Started at phase <n>: work committed before this run was covered by the whole suite, not read as a diff, its static-check findings in the baseline.'
  # Each narrowed core rule, named by its exact text (constitution I).
  'For completed tasks, make sure to mark the task off as [X]'
  'parallel tasks [P] can run together'
  'Halt execution if any non-parallel task fails'
)
for phrase in "${phrases[@]}"; do
  grep -qF -- "$phrase" <<< "$said" || problem "the fragment does not say '$phrase'"
done
# The fragment's first paragraph after its heading says which rule applies in
# a project that is not a git repository, such as a contained run's export of
# one with no `.git`: The call sends the run to Fallback. It is a statement of
# what The call and Fallback already say, so it must stay the first thing a
# reader meets and must not claim more than those two do. The whole paragraph
# is compared, so a rewording that adds a claim turns this red; so does moving
# it down or dropping it. Checked in the composed skill too.
inert='In a project that is not a git repository, such as an export of one without its `.git`, **The call** sends the run to **Fallback**: the remaining tasks are carried out in this session as core does, and the completion report says which and why.'
"$PY" -c 'import sys
squeeze = lambda t: " ".join(t.split())
paragraphs = [squeeze(p) for p in open(sys.argv[1], encoding="utf-8").read().split("\n\n") if p.strip()]
sys.exit(not (paragraphs[0] == "## Story workers" and paragraphs[1] == sys.argv[2]))' \
  implement.md "$inert" ||
  problem "the fragment's first paragraph after its heading is not the not-a-git-repository line"
grep -qF -- "$inert" <<< "$(tr -s '[:space:]' ' ' < "$(skill_of speckit.implement)")" ||
  problem "the composed speckit-implement skill does not carry the not-a-git-repository line"
# 0.1.0's Resume rule, replaced in 0.2.0: it restarted a feature adopted
# partway through at Phase 1.
for phrase in 'A run starts at the phase after the last commit whose message contains' \
  'on resume, the uncommitted diff' 'temporary `git worktree`' 'Resumed at phase' \
  "the baseline is HEAD at the run's start" 'what earlier workers finished' \
  'Changes made before the run' 'beyond that record' \
  "it commits before the next phase's worker starts"; do
  ! grep -qF -- "$phrase" <<< "$said" || problem "the fragment still says '$phrase'"
done

# 004 (US1): the fragment is one rule per bullet, and the bullets are the mapping of
# specs/004-fragment-form-and-observation/plan.md, one inventoried rule each. Read from HEAD, like
# the fragment. Whether a bullet still MEANS what the clause it replaced did is not decidable
# here: a fresh-context reviewer compares the inventory with the old and the new text.
feature=specs/004-fragment-form-and-observation
for f in "$feature/plan.md" "$feature/spec.md" README.md; do
  git -C "$PRESET" show "HEAD:$f" > "$work/$(basename "$f")" 2> /dev/null || problem "no $f at HEAD"
done
rules() { "$PY" "$PRESET/tests/fragment_rules.py" "$1" plan.md spec.md README.md; }
rules "$(skill_of speckit.implement)" || fail=1
# Seen red (constitution III, specs/004 SC-001): a bullet removed, one duplicated, one reworded,
# an inventory row dropped, a justification sentence dropped from the README. Each must fail,
# naming the rule.
break_check() { # <what> <id it must name> <python expression on `text` (the skill) or `spec`>
  "$PY" -c 'import sys
skill, spec, readme = (open(p, encoding="utf-8").read() for p in sys.argv[2:5])
exec(sys.argv[1])
open("broken-skill.md", "w", encoding="utf-8").write(skill)
open("broken-spec.md", "w", encoding="utf-8").write(spec)
open("broken-readme.md", "w", encoding="utf-8").write(readme)' "$3" "$(skill_of speckit.implement)" spec.md README.md
  if said=$("$PY" "$PRESET/tests/fragment_rules.py" broken-skill.md plan.md broken-spec.md broken-readme.md); then
    problem "fragment_rules.py passed with $1"
  elif ! grep -qF -- "$2" <<< "$said"; then
    problem "fragment_rules.py did not name $2 with $1"
  fi
}
break_check 'R7 removed' 'R7' 'skill = skill.replace("- Never run two workers at once.\n", "")'
break_check 'R7 duplicated' 'R7' 'skill = skill.replace("- Never run two workers at once.\n", "- Never run two workers at once.\n" * 2)'
break_check 'R7 reworded' 'R7' 'skill = skill.replace("Never run two workers at once.", "Do not run two workers at once.")'
break_check 'R50 added to the fragment as an extra bullet' 'mapping lacks' 'skill = skill.rstrip() + "\n- Also do a thing.\n"'
break_check 'R7 dropped from the inventory' 'R7' 'spec = spec.replace("| R7 |", "| X7 |")'
break_check 'J3 dropped from the README' 'J3' 'readme = readme.replace("**J3**", "J3")'
[ "$fail" -ne 0 ] || echo "ok: US1, the fragment is the mapping; each hand-break turned fragment_rules.py red"

specify version > version.txt 2>&1 || true
[ "$fail" -eq 0 ] && echo "ok: composes on specify $(grep -m1 -oE '[0-9]+\.[0-9]+\.[0-9]+' version.txt)"
exit "$fail"
