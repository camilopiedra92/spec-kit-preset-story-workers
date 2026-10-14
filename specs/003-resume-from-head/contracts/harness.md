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
- Before the first worker the run records `git status --porcelain`: the files it lists were changed
  before the run and are the user's: no finding, no question, no stop; no worker edits, stages,
  commits or reverts them; a task that needs one, or a suite red because of one, goes to the main
  session, which carries out that phase's remaining items as core does. Verification also requires
  `git status --porcelain` to list nothing beyond that record and `tasks.md`. The run's `tasks:`
  commits carry `tasks.md` as it stands.
- A task found already done is marked on the suite, the static checks and the main session's
  reading of the commit or file the worker cites.
- `Project Setup Verification` is Phase 1's worker's only.
- In a git repository the completion report carries `Started at phase <n>: work committed before
  this run was covered by the whole suite, not read as a diff, its static-check findings in the
  baseline.`; with every task marked, no worker starts, nothing is committed, and the report says so
  in its place.
- `compose.sh` requires a phrase per clause and refuses the 0.1.0 clauses (`A run starts at the
  phase after the last commit whose message contains`, `on resume, the uncommitted diff`, `temporary
  git worktree`, `what earlier workers finished`) and the first draft's `Resumed at phase` and
  `the baseline is HEAD at the run's start`. A phrase shows a clause is there, not that no qualifier
  was added beside it; that is the reviewer's to read.

## `tests/eval/run.sh [--baseline <run-dir>] [--state <name>] <fixture> <arm> <out-dir>`

`--state <name>` copies `fixtures/<fixture>/states/<name>/` as committed (`git archive`) over the
scratch project before the setup commit; refused (exit 2) when the directory is not committed.
`versions.txt` adds `state: <name>` (`state: -` without the flag), a pre-run key.

## `tests/eval/resume_check.py <out-dir>`

Reads `status`, `versions.txt` (`fixture`, `state`, `commit`), `commits.txt`, `stream.jsonl`,
`heldout.txt`, `report.txt`, `repo/<feature>/tasks.md` (the run's final one), and the fixture and
its state at the run's commit. Prints one line per check (`ok` / `FAIL …`): `finished phases
untouched` (no commit changes a file the state holds that no unfinished phase's task names), `first
brief opens the first unfinished phase`, `no brief opens a finished phase`, `every task marked`, `no
question asked`, `held-out N of N`, `report names the start` (FR-005's whole line). Exit 0 all ok,
1 one fails, 2 unreadable input or a status other than `ok`.
