# Feature Specification: Resume from HEAD

**Feature Branch**: `003-resume-from-head`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Resume as a fresh start from HEAD: a run resumes at the first phase
that has a task not marked in tasks.md, with HEAD at the run's start as its baseline, so a project
that installs the preset partway through a feature resumes where it is; measured by an eval before
release as 0.2.0." (decided by the owner on 2026-10-14, after two history-based fixes failed fresh
review)

## Context

`v0.1.0`'s fragment resumes after its own last `tasks: mark phase <n>` commit. A project that
installs the preset partway through a feature has no such commit, so the run restarts at Phase 1
and re-verifies finished phases: found by the fresh review of the install on supertrader, whose
feature 001 has eight of nine phases done.

Two fixes that reconstructed "what was already verified" from git history failed fresh review
(closed PR #4): a Phase 1 interruption put the baseline after the commits it had to verify; a task
left unmarked on purpose (a hook blocked it) reopened a finished phase; and a fresh run stopped to
ask about uncommitted spec files, a refusal constitution IV forbids. History can come from this
preset, from core, from a hook or from the user, and each rule that reads it breaks on some mix.

This feature stops reconstructing. `tasks.md`'s marks are core's own record of what is done (core
`speckit-implement`: "For completed tasks, make sure to mark the task off as [X]"); a resumed run
takes them as they are and starts from the repository as it finds it.

## Clarifications

### Session 2026-10-14

- Q: How does a run decide what is done? → A: from `tasks.md`'s marks, `[X]` or `[x]`, as core
  records them; nothing is read from commit messages for it.
- Q: What is a resumed phase verified against? → A: (superseded below: each phase's baseline is
  HEAD before its first worker, as Verification says.) Work committed before the run is covered by
  the whole-suite run, not by a diff reading, and the completion report says so.
- Q: What happens to uncommitted changes when a run starts? → A: what core does: they stay in the
  working tree; the run neither asks nor stops (made precise below).
- Q: Is the rule measured? → A: yes, before release (constitution III): a resume eval on a fixture
  with Phase 1 done, plus a check that a fresh run is unchanged. Released as 0.2.0, a MINOR
  version: behaviour changes for resumed runs (constitution V).

### Session 2026-10-14 (after the fragment's fresh review)

- Q: Are a fresh and a resumed run told apart? → A: no. Every run reads the marks the same way;
  the brief always says an unmarked task may already be done; the report always carries `Started at
  phase <n>:` in a git repository. A run interrupted in Phase 1 before anything was marked would
  otherwise count as fresh and lose both.
- Q: Where are the marks read? → A: from `tasks.md` as core reads it, the working tree; the main
  session only marks after verification, so uncommitted marks are verified ones.
- Q: What about changes uncommitted when the run starts? → A: they are not the run's: not a
  finding, never committed or reverted by the run; the diff reading covers the commits the run made
  since the recorded HEAD; a worker stages only the files it changed.
- Q: What about phases all marked after the start point? → A: every phase whose tasks are all
  marked is skipped, wherever it falls; with every task marked, no worker starts and nothing is
  committed.

### Session 2026-10-14 (after the second fresh review)

- Q: How are changes made before the run kept apart from the run's? → A: the run records `git
  status --porcelain` before the first worker. No worker edits, stages, commits or reverts a file it
  lists; a task that needs one, or a suite red because of one, goes to the main session, which
  carries out that phase's remaining items as core does. Verification also requires the working
  tree to list nothing beyond that record and `tasks.md`, so a worker's uncommitted leftover is a
  finding. The run's own `tasks.md` commits carry the file as it stands, earlier edits included.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A feature started without the preset resumes where it is (Priority: P1)

A developer installs the preset on a project whose feature is partly built, with earlier phases'
tasks marked done, and runs `/speckit-implement`. The run starts at the first phase that still has
an unmarked task, leaves the finished phases alone, hands the worker only that phase's unmarked
tasks, told to check what of them the repository already holds, and finishes the feature.

**Why this priority**: it is the defect: today such a run restarts at Phase 1.

**Independent Test**: the resume eval (User Story 3): on a fixture with Phases 1–2 done, one run
with the preset makes no commit that touches a file only those phases name, does not stop, and ends
with every held-out test passing.

**Acceptance Scenarios**:

1. **Given** a feature whose first phases' tasks are all marked and committed and whose later
   phases are untouched, **When** `/speckit-implement` runs with the preset, **Then** the first
   worker is briefed with the first unfinished phase's tasks, and no commit of the run changes a
   file only the finished phases' tasks name.
2. **Given** a phase with some tasks marked and some not, **When** the run reaches it, **Then** its
   worker is briefed with only the unmarked tasks, and told that some may already be done in
   whole or in part, to check each against the code and `git log`, and to complete only what is
   missing.
3. **Given** a task left unmarked in an earlier phase (a hook blocked it), **When** a later run
   starts, **Then** it resumes at that phase, briefs the worker with that one task, and does not
   treat the later phases' work as that phase's to redo.
4. **Given** uncommitted changes in the working tree, **When** a run starts, **Then** it neither
   asks nor stops, as core would not, and no commit or revert of the run touches them.
5. **Given** a run in a git repository, **When** it finishes, **Then** its completion report names
   the phase it started at and says that work committed before the run was covered by the whole
   suite but not read as a diff.
6. **Given** phases all marked after an unfinished one, **When** the run reaches them, **Then** it
   skips them.

---

### User Story 2 - A fresh run is unchanged (Priority: P1)

A developer runs `/speckit-implement` on a feature with no task marked, on a clean working tree.
The run behaves as in `v0.1.0` for what is verified and marked: Phase 1 first, baseline at HEAD
before each phase's first worker, every phase verified and marked as before. It differs only in
what every run now does: the brief's note that an unmarked task may already be done and its list of the phases already
marked (in place of what earlier workers finished); the worker staging only its own files; the
report slot for tasks found done; Verification reading the run's commits and `git status` against
the record at the start (in place of the diff from the recorded HEAD); no `tasks: mark phase`
commit when a phase marked nothing new; the `Started at phase 1:` line.

**Why this priority**: the change must not move the measured path (Evals 001 and 002).

**Independent Test**: the fresh-run checks that already run (the composition test's phrases) still
pass, and the fresh `with` path of the eval harness is untouched; the resume eval's own fixture
starts with Phase 1 done, so a fresh run is checked by the composed fragment's text and by the
unchanged harness tests, not by a new paid run.

**Acceptance Scenarios**:

1. **Given** no task marked, **When** a run starts, **Then** it starts at Phase 1 with the baseline
   at HEAD, verifying and marking as `v0.1.0` does.

---

### User Story 3 - The release carries its measurement (Priority: P2)

The owner releases `0.2.0` only after the resume eval passes, with its result in the README as
constitution III asks, and the owner's setup moves to it.

**Why this priority**: constitution III: a changed rule ships with an eval.

**Independent Test**: the README holds the resume eval's entry (date, fixture, what was compared,
runs, versions, result); `preset.yml`, the CHANGELOG and the tag agree on `0.2.0`; dotfiles'
`sdd-init` installs `v0.2.0`; supertrader's `main` has `v0.2.0`, merged into its feature 001.

**Acceptance Scenarios**:

1. **Given** the resume eval passes, **When** the release is made, **Then** `0.2.0` is tagged,
   the README records the eval, and the CHANGELOG entry names what changed.
2. **Given** the resume eval fails, **When** it is recorded, **Then** no release is made, and the
   result goes to the owner.
3. **Given** `v0.2.0` is tagged, **When** the owner's setup moves to it, **Then** `sdd-init`
   installs it (its check seen red first), and supertrader's `main` updates to it and is merged into
   feature 001, leaving the owner's uncommitted work untouched.

### Edge Cases

- **Every task marked**: nothing to resume; the run says so in its completion report and starts no
  worker.
- **`tasks.md` not committed** (a fresh feature): its marks are read from the working tree, as core
  reads them, always; with none marked, the run starts at Phase 1.
- **No git repository**: the fallback to core already applies (FR-007 of 001); the resume point is
  still the first unmarked task, as core would continue.
- **Commits or uncommitted changes already hold part of an unmarked task** (an interrupted run of
  this preset, or core's own work): committed parts, the worker finds by checking the code and `git
  log` and does not redo; uncommitted parts are changes made before the run, so the task goes to the
  main session, carried out as core does; the diff reading covers only the commits the new run
  makes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fragment MUST start a run at the first phase of `tasks.md` that has a task not
  marked `[X]` or `[x]`, reading the marks from the file as core does, skip every phase whose tasks
  are all marked wherever it falls, start no worker when every task is marked, and MUST NOT read
  where a run starts from commit messages.
- **FR-002**: Each phase's static-check baseline MUST be HEAD before its first worker, as for any
  phase; the diff reading MUST cover the commits made since it; no baseline is taken from history.
- **FR-003**: Every worker brief MUST carry only the phase's unmarked tasks, and MUST tell the
  worker that some may already be done in whole or in part, to check each against the code and
  `git log`, and to complete only what is missing; the worker's report MUST list tasks found already
  done, with the commit or file that holds each; the main session marks those on the suite, the
  static checks and its reading of the commit or file cited.
- **FR-004**: Changes uncommitted when a run starts MUST NOT be the run's: the run records `git
  status --porcelain` before the first worker, neither asks about the files it lists nor stops for
  them, counts them as no finding, and no worker edits, stages, commits or reverts them; a task that
  needs one, or a suite red because of one, is carried out in the main session as core does; a
  worker stages only the files it changed; Verification requires the tree to list nothing beyond
  that record and `tasks.md`; the run's `tasks.md` commits carry the file as it stands.
- **FR-005**: In a git repository, every run that starts a worker MUST end its completion report
  with `Started at phase <n>: work committed before this run was covered by the whole suite, not
  read as a diff, its static-check findings in the baseline.`; a run with every task marked says so
  in its place.
- **FR-006**: A run with no task marked on a clean working tree MUST verify, mark and commit as
  `v0.1.0` does; its differences, named in the CHANGELOG, are: the brief's note that an unmarked task may already be done and its list of the phases already
  marked (in place of what earlier workers finished); the worker staging only its own files; the
  report slot for tasks found done; Verification reading the run's commits and `git status` against
  the record at the start (in place of the diff from the recorded HEAD); no `tasks: mark phase`
  commit when a phase marked nothing new; the `Started at phase 1:` line.
- **FR-007**: The composition test MUST check each clause of FR-001 to FR-005 in the fragment and
  MUST fail if a `v0.1.0` resume clause is still there; each check seen red once.
- **FR-008**: A resume eval MUST exist under `tests/` (the `checkout` fixture in a state with Phases
  1–2 done, marked and committed) and be run once with the preset before release; it passes when no
  commit of the run changes a file only finished phases' tasks name, the first worker is briefed
  with the first unfinished phase and no brief opens a finished one, the run exits normally with
  every task marked and no question asked, every held-out test passes, and the report carries
  FR-005's line for the phase it started at. Finished phases' files are those the state holds that
  no unfinished phase's task names.
- **FR-009**: `0.2.0` MUST be released only on a passing resume eval, with the README entry,
  CHANGELOG entry and tag of constitutions III and V; then dotfiles' `sdd-init` MUST install it
  (its check seen red first) and supertrader's `main` MUST move to it and be merged into feature
  001, with the owner's uncommitted work untouched.

### Key Entities

- **Resume point**: the first phase with an unmarked task.
- **Resume eval**: the `checkout` fixture in a state with Phases 1–2 done, run once with the
  preset; its pass conditions are FR-008's.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the resume eval, 0 commits of the run change a file only finished phases' tasks
  name.
- **SC-002**: In the resume eval, the run exits normally, with no stop or question in its stream.
- **SC-003**: In the resume eval, every held-out test passes.
- **SC-004**: The composition test is green, and each new check was seen red once.
- **SC-005**: After the release, a new repository from `sdd-init` and supertrader's feature 001 both
  have `v0.2.0` installed.

## Assumptions

- One counted resume run is enough: the eval checks a behaviour (not redoing Phase 1, not
  stopping), not a cost comparison; the README calls it directional.
- The resume fixture reuses 002's `checkout` fixture with its Phases 1–2 already implemented from
  the reference (US1 only), marked and committed, so no new feature is written.
- The cost question is unchanged since 002 and out of scope.
