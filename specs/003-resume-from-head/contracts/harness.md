# Contract: 003's changes

## Where a run starts (replaces 001 contract §10)

- The marks, `[X]` or `[x]`, are read from `tasks.md` as core reads it (the working tree). Where a
  run starts is never read from commit messages.
- A run skips every phase whose tasks are all marked, wherever it falls, and starts at the first
  phase with an unmarked task (Phase 1 when none is marked). With every task marked, no worker
  starts and the completion report says so.
- Each phase's baseline is taken as Verification says (HEAD before its first worker); the diff
  reading covers the commits made since it.
- Every brief carries only the phase's unmarked tasks and says some may already be done, in whole
  or in part: check each against the code and `git log`, complete only what is missing. The
  worker's report lists tasks found already done, with the commit or file holding each; the main
  session marks them on the suite and the static checks. A phase that marks nothing new has no
  `tasks: mark phase` commit.
- A worker stages only the files it changed, never `git add -A` or `-a`.
- Changes uncommitted when the run starts are not the run's: no finding, never committed or
  reverted by the run, no question, no stop.
- In a git repository the completion report carries `Started at phase <n>: work committed before
  this run was covered by the whole suite, not read as a diff.`
- `compose.sh` requires a phrase per clause and refuses the 0.1.0 clauses (`A run starts at the
  phase after the last commit whose message contains`, `on resume, the uncommitted diff`, `temporary
  git worktree`, `what earlier workers finished`) and the first draft's `Resumed at phase` and
  `the baseline is HEAD at the run's start`.

## `tests/eval/run.sh [--baseline <run-dir>] [--state <name>] <fixture> <arm> <out-dir>`

`--state <name>` copies `fixtures/<fixture>/states/<name>/` as committed (`git archive`) over the
scratch project before the setup commit; refused (exit 2) when the directory is not committed.
`versions.txt` adds `state: <name>` (`state: -` without the flag), a pre-run key.

## `tests/eval/resume_check.py <out-dir>`

Reads `status`, `versions.txt` (`fixture`, `state`, `commit`), `commits.txt`, `stream.jsonl`,
`heldout.txt`, `report.txt`, and the fixture and its state at the run's commit. Prints one line per
check (`ok` / `FAIL …`): `finished phases untouched`, `first brief opens the first unfinished
phase`, `held-out N of N`, `report names the start`. Exit 0 all ok, 1 one fails, 2 unreadable
input or a status other than `ok`.
