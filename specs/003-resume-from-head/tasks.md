---

description: "Task list for 003-resume-from-head"
---

# Tasks: Resume from HEAD

**Input**: `specs/003-resume-from-head/` (spec, plan, research, contracts/harness.md, quickstart)

**Tests**: requested for logic of its own: the fragment's clauses (compose.sh phrases), `run.sh
--state`, `resume_check.py`. Test tasks first, each red run checked against its predicted reason.
Each story closes with `tests/check.sh` and a fresh-context review.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Open the feature's PR as a draft from branch `003-resume-from-head` (spec and plan committed), so `compose (pinned)` runs on every push

---

## Phase 2: User Story 1 + 2 - The Resume rule; a fresh run unchanged (Priority: P1)

**Goal**: the fragment's Resume rule as contracts/harness.md states it; a run with no task marked unchanged.

**Independent Test**: `tests/compose.sh` green, each new phrase and the refusal seen red.

### Tests (write first)

- [X] T002 [US1] In `tests/compose.sh`, require one phrase per clause of the contract's Resume rule (the resume point from `[X]` or `[x]` marks; the baseline at HEAD at the run's start; the brief's "may already be done" check; uncommitted changes left as core leaves them; the `Resumed at phase <n>:` report line; no task marked is a fresh run) and refuse the 0.1.0 sentence; commit and run it against the 0.1.0 fragment, each check red for its own phrase

### Implementation

- [X] T003 [US1] Rewrite the Resume paragraph of `commands/speckit.implement.md` to the contract, the brief's resume clause, and the completion report's `Resumed at phase <n>:` line; lines within 100 columns; T002 green unchanged
- [X] T004 [US1] Bring `specs/001-story-workers/spec.md` (edge case "A run resumes", FR-003's brief) and `specs/001-story-workers/contracts/fragment.md` (§3, §10) to the new rule

**Checkpoint**: `tests/check.sh` green; a fresh review of the fragment change against spec 003 and the constitution.

---

## Phase 3: User Story 3 - The resume eval (Priority: P2)

**Goal**: one counted resume run on `checkout` with Phases 1–2 done, judged by `resume_check.py`.

### Tests (write first)

- [ ] T005 [P] [US3] Extend `tests/eval/test_run.py`: `--state <name>` overlays the committed `fixtures/<f>/states/<name>/` before the setup commit; an uncommitted or missing state is refused (exit 2); `versions.txt` has `state:` among the pre-run keys
- [ ] T006 [P] [US3] Write `tests/eval/test_resume_check.py` against synthetic run directories: each check passes and fails on its own (a commit touching a finished-only file; the first worker brief opening another phase; a held-out score below N; no `Resumed at phase` line, or one naming another phase); exit 2 on unreadable input or a non-`ok` status
- [ ] T007 [US3] Red run of T005–T006 against a stub `resume_check.py` and the unchanged `run.sh`

### Implementation

- [ ] T008 [US3] `tests/eval/run.sh --state <name>` (contract); usage line and header
- [ ] T009 [US3] `tests/eval/resume_check.py` (contract; research R3), stdlib, typed
- [ ] T010 [US3] Write `tests/eval/fixtures/checkout/states/phase-2-done/`: `tasks.md` with T001–T011 marked `[X]`, and Phases 1–2's files (the reference's US1 code without US2 and US3, and the US1 test files); prove it: the held-out tests of US1 pass against it, and those of US2 and US3 fail for want of their code
- [ ] T011 [US3] Green run: T005–T006 unchanged; `tests/check.sh` green

### The measurement (spends usage; the owner confirms first)

- [ ] T012 [US3] Step 0 (check, probes, oracle); show the estimate; **owner confirms**; run quickstart's resume run; `resume_check.py` on it
- [ ] T013 [US3] Commit the run's files under `tests/eval/results/003-resume-from-head/` (no stream, no transcripts) and write the README's Eval 003 entry (date, fixture and state, what was checked, one run, versions, result)

**Checkpoint**: a fresh review of US3 (harness, state, the README entry against the committed outputs). Pass → Phase 4; fail → the result goes to the owner, no release.

---

## Phase 4: Release and adoption

- [ ] T014 `preset.yml` 0.2.0, `CHANGELOG.md` 0.2.0 (Changed: the Resume rule; the eval), README status and install URL, `CLAUDE.md`'s version mention
- [ ] T015 `/speckit-converge` until a pass finds nothing above LOW
- [ ] T016 Fresh review of the whole PR; **the owner reviews against constitution I–V**; on approval, mark ready, `gh pr merge --auto --squash` on green, tag `v0.2.0`, and install from the tag in a scratch repository
- [ ] T017 Dotfiles: `sdd-init`'s story-workers URL to `v0.2.0` (the check pins the shape, so no red is owed for a version move), `./check.sh`, a real `sdd-init` in a scratch repository, PR draft → fresh review → ready → merge on green
- [ ] T018 supertrader: on `main`, `specify preset update story-workers --from <v0.2.0>` in a worktree, a fresh-context review (its governance), commit; then merge `main` into `001-truthful-market-simulation` with the owner's uncommitted work untouched (git refuses on overlap)

## Dependencies

Phase 1 → Phase 2 → Phase 3 (the run needs the fragment) → Phase 4. T012 waits for the owner's
confirmation; T016 for the owner's review.
