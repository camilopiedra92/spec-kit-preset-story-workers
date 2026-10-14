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
  worker's report lists tasks found already done, with the commit or file holding each. A phase that marks nothing new has no
  `tasks: mark phase` commit.
- A worker stages only the files it changed, never `git add -A` or `-a`.
- Before the first worker the run runs `git status --porcelain --untracked-files=all`. A path
  outside the feature directory sends the whole run to core (Fallback), the completion report
  naming those paths. Inside the feature directory, uncommitted changes stay as they are: no
  finding, no question, no stop; no worker edits, stages, commits or reverts a file there; a task
  that changes one is carried out in the main session as core does and left uncommitted. The run's
  `tasks:` commits carry `tasks.md` as it stands. A worker commits Project Setup Verification's
  changes in a commit of their own. The main session commits what it changes outside the feature
  directory before the next phase's worker (`tasks: carried out in this session`). Verification
  requires `git status --porcelain --untracked-files=all`, run before its own runs, to list nothing
  outside the feature directory; what it lists is the worker's, and goes back to it as a
  finding.
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

`--state <name>` copies `fixtures/<fixture>/states/<name>/committed/` as committed (`git archive`)
over the scratch project before the setup commit, and `states/<name>/uncommitted/`, when there is
one, after every commit, so the agent finds it changed and not committed; refused (exit 2) when
`committed/` is not committed. `commits.txt` is written with `--no-renames`, so a moved file shows
its old path too.
`versions.txt` adds `state: <name>` (`state: -` without the flag), a pre-run key.

## `tests/eval/resume_check.py <out-dir>`

Reads `status`, `versions.txt` (`fixture`, `state`, `commit`), `commits.txt`, `stream.jsonl`,
`heldout.txt`, `report.txt`, `repo/<feature>/tasks.md` (the run's final one), and the fixture and
its state at the run's commit. Prints one line per check (`ok` / `FAIL …`): `finished phases
untouched` (a file the state's `committed/` holds that no unfinished phase's task names is in no
commit, and the run's tree holds it as the state does), `uncommitted changes untouched` (each file
of `uncommitted/` is in no commit, and the tree holds it as the state does), `first
brief opens the first unfinished phase`, `no brief opens a finished phase`, `every task marked`, `no
question asked`, `held-out N of N`, `report names the start` (FR-005's whole line). Exit 0 all ok,
1 one fails, 2 unreadable input or a status other than `ok`.
