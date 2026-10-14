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
- Q: What is a resumed phase verified against? → A: HEAD at the run's start, as a fresh run is:
  the static-check baseline and the diff reading start there. Work committed before the run is
  covered by the whole-suite run, not by a diff reading, and the completion report says so.
- Q: What happens to uncommitted changes when a run starts? → A: what core does: they stay in the
  working tree; the run neither asks nor stops.
- Q: Is the rule measured? → A: yes, before release (constitution III): a resume eval on a fixture
  with Phase 1 done, plus a check that a fresh run is unchanged. Released as 0.2.0, a MINOR
  version: behaviour changes for resumed runs (constitution V).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A feature started without the preset resumes where it is (Priority: P1)

A developer installs the preset on a project whose feature is partly built, with earlier phases'
tasks marked done, and runs `/speckit-implement`. The run starts at the first phase that still has
an unmarked task, leaves the finished phases alone, hands the worker only that phase's unmarked
tasks, told to check what of them the repository already holds, and finishes the feature.

**Why this priority**: it is the defect: today such a run restarts at Phase 1.

**Independent Test**: the resume eval (User Story 3): on a fixture with Phase 1 done, one run with
the preset makes no commit that touches Phase 1's files, does not stop, and ends with every held-out
test the remaining phases cover passing.

**Acceptance Scenarios**:

1. **Given** a feature whose Phase 1 tasks are all marked and committed and whose later phases are
   untouched, **When** `/speckit-implement` runs with the preset, **Then** the first worker is
   briefed with Phase 2's tasks, and no commit of the run changes a file only Phase 1's tasks name.
2. **Given** a phase with some tasks marked and some not, **When** the run reaches it, **Then** its
   worker is briefed with only the unmarked tasks, and told that some may already be done in
   whole or in part, to check each against the code and `git log`, and to complete only what is
   missing.
3. **Given** a task left unmarked in an earlier phase (a hook blocked it), **When** a later run
   starts, **Then** it resumes at that phase, briefs the worker with that one task, and does not
   treat the later phases' work as that phase's to redo.
4. **Given** uncommitted changes in the working tree, **When** a run starts, **Then** it neither
   asks nor stops, as core would not.
5. **Given** a resumed run, **When** it finishes, **Then** its completion report says that work
   committed before the run was covered by the whole suite but not read as a diff.

---

### User Story 2 - A fresh run is unchanged (Priority: P1)

A developer runs `/speckit-implement` on a feature with no task marked. The run behaves as in
`v0.1.0`: Phase 1 first, baseline at HEAD before the first worker, every phase verified and marked
as before.

**Why this priority**: the change must not move the measured path (Evals 001 and 002).

**Independent Test**: the fresh-run checks that already run (the composition test's phrases) still
pass, and the fresh `with` path of the eval harness is untouched; the resume eval's own fixture
starts with Phase 1 done, so a fresh run is checked by the composed fragment's text and by the
unchanged harness tests, not by a new paid run.

**Acceptance Scenarios**:

1. **Given** no task marked, **When** a run starts, **Then** it starts at Phase 1 with the baseline
   at HEAD, exactly as `v0.1.0` does.

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
  reads them; with none marked, it is a fresh run.
- **No git repository**: the fallback to core already applies (FR-007 of 001); the resume point is
  still the first unmarked task, as core would continue.
- **Commits or uncommitted changes already hold part of an unmarked task** (an interrupted run of
  this preset, or core's own work): the worker finds them by checking the code and `git log`, and
  does not redo them; the main session's diff reading covers only what the new run changes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fragment MUST resume at the first phase of `tasks.md` that has a task not marked
  `[X]` or `[x]`, and MUST NOT read the resume point from commit messages.
- **FR-002**: A resumed phase's static-check baseline and diff reading MUST start at HEAD at the
  run's start; no baseline is taken from history.
- **FR-003**: A resumed phase's worker brief MUST carry only the phase's unmarked tasks, and MUST
  tell the worker that some may already be done in whole or in part, to check each against the code
  and `git log`, and to complete only what is missing: the worker judges what is done, no rule
  reconstructs it from history.
- **FR-004**: A run MUST leave uncommitted changes as core does: it neither asks about them nor
  stops for them.
- **FR-005**: A resumed run's completion report MUST say that work committed before the run was
  covered by the whole-suite run but not read as a diff.
- **FR-006**: A run with no task marked MUST behave as `v0.1.0` does.
- **FR-007**: The composition test MUST check each clause of FR-001 to FR-005 in the fragment and
  MUST fail if the `v0.1.0` resume rule is still there; each check seen red once.
- **FR-008**: A resume eval MUST exist under `tests/` (a fixture with Phase 1 done, marked and
  committed, the preset installed) and be run once with the preset before release; it passes when
  no commit of the run changes a file only Phase 1's tasks name, the run exits normally without a
  stop or a question, and every held-out test of the remaining phases passes.
- **FR-009**: `0.2.0` MUST be released only on a passing resume eval, with the README entry,
  CHANGELOG entry and tag of constitutions III and V; then dotfiles' `sdd-init` MUST install it
  (its check seen red first) and supertrader's `main` MUST move to it and be merged into feature
  001, with the owner's uncommitted work untouched.

### Key Entities

- **Resume point**: the first phase with an unmarked task.
- **Resume eval**: a fixture whose Phase 1 is done, run once with the preset; its pass conditions
  are FR-008's.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the resume eval, 0 commits of the run change a file only Phase 1's tasks name.
- **SC-002**: In the resume eval, the run exits normally, with no stop or question in its stream.
- **SC-003**: In the resume eval, every held-out test the remaining phases cover passes.
- **SC-004**: The composition test is green, and each new check was seen red once.
- **SC-005**: After the release, a new repository from `sdd-init` and supertrader's feature 001 both
  have `v0.2.0` installed.

## Assumptions

- One counted resume run is enough: the eval checks a behaviour (not redoing Phase 1, not
  stopping), not a cost comparison; the README calls it directional.
- The resume fixture reuses 002's `checkout` fixture with its Phase 1 already implemented from the
  reference, marked and committed, so no new feature is written.
- The cost question is unchanged since 002 and out of scope.
