# Research: Resume from HEAD

Features 001 and 002's research holds for everything this feature does not change. Closed PR #4's
two fresh reviews (2026-10-14) are the evidence for R1's rejected alternatives.

## R1. What a resumed run trusts

- **Decision**: `tasks.md`'s marks, `[X]` or `[x]`, read as core reads them (the working tree),
  decide where a run starts: every all-marked phase is skipped, wherever it falls. Each phase's
  baseline is HEAD before its first worker, as Verification already says. Every run is treated
  alike: the brief always says an unmarked task may already be done (check against the code and
  `git log`, complete only what is missing), the worker's report lists tasks found done, and the
  completion report always carries `Started at phase <n>:`, since work committed before the run is
  covered by the suite and not read as a diff. Uncommitted work is kept apart by a clean tree
  outside the feature directory (R4).
- **Rationale**: the marks are core's own record ("For completed tasks, make sure to mark the task
  off as [X]"); everything else a run could read about past work (commit messages, which commit
  touched what) comes from several writers and was misread in every reconstruction reviewed.
  Judging partial work is a reading task, which the worker does with the code in front of it.
- **Alternatives considered**: *resume after the last `tasks: mark phase` commit* (0.1.0): restarts
  an adopted feature at Phase 1. *Baseline at the last commit that changed `tasks.md`*: falls
  mid-phase on a found-tasks commit, and before finished phases in an adopted feature (PR #4,
  review 1). *Baseline at the last marker commit, else HEAD, and ask about uncommitted work*: a
  Phase 1 interruption puts the baseline after the commits to verify; a hook-blocked task reopens a
  finished phase; a fresh run stops to ask about uncommitted spec files, a refusal constitution IV
  forbids (PR #4, review 2). *Brief the worker with "the commits since the last finished phase"*:
  the same reconstruction, moved into the brief.
- **Alternatives after the fragment's fresh review** (2026-10-14): *telling a fresh run from a
  resumed one*: a Phase 1 interruption with nothing marked counts as fresh, so its worker redoes
  committed work and the report hides the unread commits; treating every run alike costs one
  vacuous line on a clean fresh run. *Marks as committed at HEAD*: an adopted feature whose marks
  were never committed restarts at Phase 1, the defect itself; the main session marks only after
  verification, so working-tree marks are verified ones. *Leaving the diff reading and staging as
  0.1.0 had them*: pre-run uncommitted changes became findings a fix worker could revert, and a
  worker's `git add -A` could commit them.
- **Accepted limit**: a run does not diff-read work committed before it. Stated in the completion
  report, so the user knows which work had only the suite. A task a hook blocks stays unmarked, so
  each later run starts at its phase and costs one worker to find it still blocked.

## R2. The resumed state for the eval

- **Decision**: `tests/eval/run.sh --state <name>` overlays `fixtures/<fixture>/states/<name>/
  committed/` onto the copied project before the setup commit, and `uncommitted/`, when present,
  after it, so the agent finds it changed; `versions.txt` records `state: <name>`. The
  state `phase-2-done` of `checkout` holds Phases 1–2 implemented (the reference's US1 code, without
  US2 and US3, and the US1 test files a worker would have written) and `tasks.md` with T001–T011
  marked `[X]`, and in `uncommitted/` an HTML comment appended to the feature's `spec.md`, as an
  owner's note left uncommitted (R4). `price` keeps `plan.md`'s signature (`promotions`, `discount_cap`) and refuses a
  promotion or a cap with `NotImplementedError` until User Story 2: the held-out helper always
  passes both, so without them no US1 pricing test could pass; US1's literal signature, the
  alternative, would leave the state unproven. Proven 2026-10-14: the state's suite 19 passed;
  held-out 18 passed (every US1 test), 41 failed, each on the missing `checkout.promotions` (35)
  or `checkout.returns` (6) module.
- **Rationale**: the held-out tests, their N and the reference stay the fixture's own: one copy,
  one oracle. The state is committed, so the eval is rerunnable.
- **Alternatives considered**: *a second fixture with its own copy of the held-out tests*: two
  copies of 59 tests to keep in step. *A symlinked `heldout/`*: `git archive` stores the link, not
  the files. *Building the state by running core on Phases 1–2 first*: costs a run, and the state
  would differ each time.

## R3. The pass conditions, checked by a script

- **Decision**: `tests/eval/resume_check.py <out-dir>` reads the run's committed files and the
  fixture (at the run's commit) and prints, each `ok` or `FAIL`: no commit of the run changes a
  file the state's `committed/` holds that no unfinished phase's task names, and the run's tree
  holds each as the state does (for `phase-2-done`:
  `src/checkout/__init__.py`, `src/checkout/tax.py`, `tests/conftest.py`, `tests/test_cart.py`,
  `tests/test_catalog.py`, `tests/test_pricing.py`, `tests/test_tax.py`; `commits.txt` is written
  with `--no-renames`, so a move shows the old path); the state's `uncommitted/` edit is in no
  commit and unchanged in the tree; the first worker's brief
  opens with the first unfinished phase's heading and no brief opens a finished one; every task of
  the run's final `tasks.md` is marked and the stream holds no `AskUserQuestion`, since a headless
  run that ends its turn on a question still exits 0; the held-out score is N of N; the report
  carries FR-005's whole line for that phase. A counted run (run.sh's own rules) is the
  precondition.
- **Limit**: US1's parts of the modules later phases also name (`cart.py`, `catalog.py`,
  `money.py`) are those phases' to change, so a rewrite of them is not seen by the first check; the
  held-out tests, US1's included, are what guard them. `tests/conftest.py` and
  `src/checkout/__init__.py` count as finished: a later worker that adds a fixture or an export to
  them fails the check, though the fixture's tasks call for neither (T001 keeps `conftest.py`
  empty).
- **Rationale**: a behaviour check, not a comparison, so one counted run decides it; the script
  records the verdict as `compare.py` does for 002: its output and its inputs are committed except
  the stream and the run's working tree (the stream holds local paths and session ids; the tree is
  not copied), so the verdict is recorded, not rebuildable from the repository; from the committed
  files alone, `every task marked`, `held-out N of N` and the report checks can be rerun.
- **Alternatives considered**: *reading the verdict by hand*: one more place for a slip, which
  002's reviews found more than once. *A `without` arm beside it*: core resumes by redoing nothing
  only because it never reads history; comparing it says nothing about the preset's rule.
- **The arm without the rule** (owner, 2026-10-14, after the fourth review; constitution III):
  `v0.1.0`, installed by `run.sh --preset v0.1.0` from its tag's archive, once on the same state.
  Its rule restarts at the phase after the last `tasks: mark phase` commit, which this state lacks,
  so it is expected to brief Phase 1 and fail `first brief opens the first unfinished phase`; its
  0.1.0 handling of uncommitted changes (a worker to finish or discard them) is expected to fail
  `uncommitted changes untouched`. The comparison is the two runs' `resume_check.py` outputs side by
  side; both are directional (one run each). *Observed* (`v010-1`): it briefed Phase 2, not Phase 1:
  a fresh review of User Story 1, then a fix worker on Phase 2 that changed `cart.py` and
  `tests/test_cart.py`, then an empty `tasks: mark phase 2` commit; it left the uncommitted note
  alone by its own judgement. It failed four checks, not `uncommitted changes untouched`.
- **A fresh run, with and without the rule** (owner, 2026-10-14, convergence T026): constitution
  III asks what the rule must not make worse, and every run follows 0.2.0's new rules (staging,
  Project Setup Verification's commit, Verification reading commits, the start check). One `0.2.0`
  and one `v0.1.0` run on `checkout` with no state, judged by the same checks (`state: -`: the start
  at Phase 1); `v0.1.0` is expected to fail only `report names the start`, its report having no
  such line; held-out, marks, questions and cost compared side by side.
- **What counts as a worker**: a main-session Agent call whose brief opens with one of the state's
  phase headings, whatever model it names (a review's prompt opens otherwise); `every task marked`
  requires each task the state names, present and marked, in the final `tasks.md`. A plain-text
  question that ends the turn is caught only through `every task marked`.
- **The rule's other parts, measured too** (owner, 2026-10-14): two states extend `phase-2-done`
  (a state's `extends` file names its base; `run.sh` and `resume_check.py` lay the chain base
  first). `phase-2-done-doc-task` adds T031, a Phase 4 task that writes `specs/001-checkout/plan.md`:
  checked by `feature-directory tasks carried out in this session` (on the report's `Carried out in
  this session:` line, the file changed, in no commit). `phase-2-done-dirty` adds an uncommitted
  `NOTES.md` at the project root: the run is core's, checked by `no worker started` and `report names
  the paths outside the feature directory`, the other checks as for any run. One `0.2.0` run each;
  no `v0.1.0` arm, the comparison being `phase-2-done`'s. *Rejected*: recording these parts for the
  owner's acceptance unmeasured, since a fixture state measures them for one run each.

## R4. Uncommitted work: a clean tree outside the feature directory

- **Decision** (owner, 2026-10-14, after the third fresh review): before the first worker the run
  runs `git status --porcelain --untracked-files=all`; a path outside the feature directory sends
  the whole run to core (Fallback), naming those paths. Inside the feature directory, uncommitted
  changes stay as they are: no worker edits, stages, commits or reverts a file there, and a task that
  changes one is carried out in the main session as core does, left uncommitted. The run's
  `tasks.md` commits carry the file as it stands. A worker stages only its own files and commits
  Project Setup Verification's changes on their own; the main session commits what it changes
  outside the feature directory before the next worker. Verification requires the same `git status`,
  run before its own runs, to list nothing outside the feature directory.
- **Rationale**: with nothing uncommitted outside the feature directory, every change there after a
  worker is that worker's, so no record is needed and none can be misread; spec artifacts, the usual
  uncommitted files at implement time, live inside the feature directory, which workers never write.
- **Alternatives considered**: *a record of `git status --porcelain` taken at the start, workers
  never touching a listed file* (second review's fix): a worker's edit to an already changed file
  leaves its status line as it was; untracked directories collapse to one line; the main session's
  own uncommitted work reads as a worker's; a red suite cannot be traced to the user's file. Patching
  it needs per-file hashes, untracked files listed one by one and a suite at the start, and each
  round found more. *Falling back to core on any uncommitted change*: spec files are usually
  uncommitted at implement time, so the preset would rarely run. *Letting a worker finish
  uncommitted partial work*: its commit would carry the user's changes.
- **Accepted limits**: a project with uncommitted work outside the feature directory runs as core
  until that work is committed: the preset's own install included (the README says to commit it),
  generated files git does not ignore (a worker adds them to the ignore file once one is found after
  it), and, in a monorepo, a sibling project's uncommitted work. A worker that writes the feature
  directory against its brief is seen in the commit reading when it commits, and the finding is
  this session's to carry out as core does; an uncommitted write there is not seen. Tasks
  that change the feature's own documents (a quickstart, a contract) are carried out in the main
  session. Both are measured (R3): the fallback on a dirty tree by `phase-2-done-dirty`, a
  task that changes the feature's documents by `phase-2-done-doc-task`, and the inside case by
  `phase-2-done`'s uncommitted edit to the feature's spec.
