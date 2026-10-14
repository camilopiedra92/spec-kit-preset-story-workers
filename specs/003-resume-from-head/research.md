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
  covered by the suite and not read as a diff. Changes uncommitted at the start are not the run's:
  the diff reading covers the run's commits, a worker stages only its own files, and nobody commits
  or reverts them.
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

- **Decision**: `tests/eval/run.sh --state <name>` overlays `fixtures/<fixture>/states/<name>/`
  onto the copied project before the setup commit; `versions.txt` records `state: <name>`. The
  state `phase-2-done` of `checkout` holds Phases 1–2 implemented (the reference's US1 code, without
  US2 and US3, and the US1 test files a worker would have written) and `tasks.md` with T001–T011
  marked `[X]`. `price` keeps `plan.md`'s signature (`promotions`, `discount_cap`) and refuses a
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
  file that only finished phases' tasks name (for `phase-2-done`: `tests/test_catalog.py`,
  `tests/test_cart.py`, `tests/test_tax.py`, `tests/test_pricing.py`, `src/checkout/tax.py`); the
  first worker's brief opens with the first unfinished phase's heading; the held-out score is N of
  N; the report has a `Started at phase <n>:` line naming that phase. A counted run (run.sh's own
  rules) is the precondition: it exited normally, so it did not stop.
- **Rationale**: a behaviour check, not a comparison, so one counted run decides it; the script
  makes the verdict reproducible from committed files, as `compare.py` does for 002.
- **Alternatives considered**: *reading the verdict by hand*: one more place for a slip, which
  002's reviews found more than once. *A `without` arm beside it*: core resumes by redoing nothing
  only because it never reads history; comparing it says nothing about the preset's rule.
