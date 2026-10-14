# Contract: 003's changes

## The fragment's Resume rule (replaces 001 contract §10)

- The resume point is the first phase of `tasks.md` with a task not marked `[X]` or `[x]` (marks as
  committed at HEAD; as in the working tree when `tasks.md` is not committed). Commit messages are
  not read for it.
- The baseline (static checks, diff reading) is HEAD at the run's start.
- On resume, the brief carries only the phase's unmarked tasks and says some may already be done in
  whole or in part: check each against the code and `git log`, complete only what is missing.
- Uncommitted changes stay as core leaves them; the run neither asks nor stops for them.
- A resumed run's completion report has a line `Resumed at phase <n>: work committed before this
  run was covered by the whole suite, not read as a diff.`
- With no task marked, the run is a fresh run, as in 0.1.0.
- `compose.sh` requires a phrase per clause and refuses `A run starts at the phase after the last
  commit whose message contains`.

## `tests/eval/run.sh [--baseline <run-dir>] [--state <name>] <fixture> <arm> <out-dir>`

`--state <name>` copies `fixtures/<fixture>/states/<name>/` as committed (`git archive`) over the
scratch project before the setup commit; refused (exit 2) when the directory is not committed.
`versions.txt` adds `state: <name>` (`state: -` without the flag), a pre-run key.

## `tests/eval/resume_check.py <out-dir>`

Reads `status`, `versions.txt` (`fixture`, `state`, `commit`), `commits.txt`, `stream.jsonl`,
`heldout.txt`, `report.txt`, and the fixture and its state at the run's commit. Prints one line per
check (`ok` / `FAIL …`): `finished phases untouched`, `first brief opens the first unfinished
phase`, `held-out N of N`, `report names the resume`. Exit 0 all ok, 1 one fails, 2 unreadable
input or a status other than `ok`.
