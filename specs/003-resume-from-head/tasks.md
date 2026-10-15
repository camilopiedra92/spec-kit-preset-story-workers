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

- [X] T002 [US1] In `tests/compose.sh`, require one phrase per clause of the contract's Resume rule (the resume point from `[X]` or `[x]` marks; the baseline at HEAD at the run's start; the brief's "may already be done" check; uncommitted changes left as core leaves them; the `Resumed at phase <n>:` report line; no task marked is a fresh run) and refuse the 0.1.0 sentence; commit and run it against the 0.1.0 fragment, each check red for its own phrase (superseded in part by T019 and T020)

### Implementation

- [X] T003 [US1] Rewrite the Resume paragraph of `commands/speckit.implement.md` to the contract, the brief's resume clause, and the completion report's `Resumed at phase <n>:` line; lines within 100 columns; T002 green unchanged (superseded in part by T019 and T020)
- [X] T004 [US1] Bring `specs/001-story-workers/spec.md` (edge case "A run resumes", FR-003's brief) and `specs/001-story-workers/contracts/fragment.md` (§3, §10) to the new rule

**Checkpoint**: `tests/check.sh` green; a fresh review of the fragment change against spec 003 and the constitution.

---

## Phase 3: User Story 3 - The resume eval (Priority: P2)

**Goal**: one counted resume run on `checkout` with Phases 1–2 done, judged by `resume_check.py`.

### Tests (write first)

- [X] T005 [P] [US3] Extend `tests/eval/test_run.py`: `--state <name>` overlays the committed `fixtures/<f>/states/<name>/` before the setup commit; an uncommitted or missing state is refused (exit 2); `versions.txt` has `state:` among the pre-run keys
- [X] T006 [P] [US3] Write `tests/eval/test_resume_check.py` against synthetic run directories: each check passes and fails on its own (a commit touching a finished-only file; the first worker brief opening another phase; a held-out score below N; no `Resumed at phase` line, or one naming another phase); exit 2 on unreadable input or a non-`ok` status (superseded in part by T019 and T020)
- [X] T007 [US3] Red run of T005–T006 against a stub `resume_check.py` and the unchanged `run.sh`

### Implementation

- [X] T008 [US3] `tests/eval/run.sh --state <name>` (contract); usage line and header
- [X] T009 [US3] `tests/eval/resume_check.py` (contract; research R3), stdlib, typed
- [X] T010 [US3] Write `tests/eval/fixtures/checkout/states/phase-2-done/`: `tasks.md` with T001–T011 marked `[X]`, and Phases 1–2's files (the reference's US1 code without US2 and US3, and the US1 test files); prove it: the held-out tests of US1 pass against it, and those of US2 and US3 fail for want of their code
- [X] T011 [US3] Green run: T005–T006 unchanged; `tests/check.sh` green

### The measurement (spends usage; the owner confirms first)

- [X] T012 [US3] Step 0 (check, probes, oracle); show the estimate; **owner confirms**; run quickstart's resume run; `resume_check.py` on it
- [X] T013 [US3] Commit the run's files under `tests/eval/results/003-resume-from-head/` (no stream, no transcripts) and write the README's Eval 003 entry (date, fixture and state, what was checked, one run, versions, result)

- [X] T019 [US1] Apply the fragment review's findings (B1, W1–W4, G1–G6, C1–C2): one rule for every run (marks from the working tree, all-marked phases skipped, every task marked starts no worker, `Started at phase <n>:` line), changes uncommitted at the start not the run's (diff reading of the run's commits, worker stages its own files), a report slot for tasks found done; compose phrases per clause and the old clauses refused, seen red first; `resume_check.py` and its tests to `Started at phase`; spec 003, contract, research and 001's docs to match; a second fresh review
- [X] T020 [US1] [US3] (superseded in part by T021) Apply the second fresh review: changes made before the run recorded with `git status --porcelain`, never touched by a worker, a task needing one carried out in this session; Verification checks the tree against that record; found-done tasks marked on the cited commit or file too; `Project Setup Verification` Phase 1's worker only; the report line names the static-check baseline; every task marked starts no worker and commits nothing; compose phrases for each inverted clause the review found undetected (seen red first); `resume_check.py`: finished files from the state, no brief for a finished phase, every task marked, no question asked, FR-005's whole line (tests seen red first); docs to match
- [X] T021 [US1] [US3] Apply the owner's design after the third review (research R4): a clean tree outside the feature directory, else the whole run as core; workers never write the feature directory; the main session commits its own work outside it; Verification requires nothing uncommitted outside it; clause checks seen red first; `run.sh --state` with `committed/` and `uncommitted/` and `--no-renames`; `resume_check.py` compares the tree with the state and checks the uncommitted edit (tests seen red first); the state split, its spec edit left uncommitted; docs to match
- [X] T022 [US1] Apply the fourth fresh review: a task changing the feature directory is not handed off; the main session commits its own work before any later Verification; the start check before any own run; generated files into the ignore file; core's hook commits are core's; the report line when a phase went to a worker; five more clause phrases, each inversion seen red; README: commit the install; docs and research limits
- [X] T023 [US3] `run.sh --preset <ref>` (tests seen red first) and the `v0.1.0` arm in quickstart, research R3, spec and plan: the comparison constitution III asks for
- [X] T024 [US3] States may extend another (`extends`, in `run.sh` and `resume_check.py`, tests seen red first); `phase-2-done-doc-task` and `phase-2-done-dirty`; `resume_check.py`'s feature-directory-task check and its core's-run mode (tests seen red first): the rule's parts `phase-2-done` does not exercise, measured instead of accepted

**Checkpoint**: a fresh review of US3 (harness, state, the README entry against the committed outputs). Pass → Phase 4; fail → the result goes to the owner, no release.
- [X] T025 [US3] Apply the US3 checkpoint review: `resume_check.py` counts any main-session Agent call briefed with a phase as a worker, whatever its model, and requires every task the state names present and marked (tests seen red first; the four recorded verdicts unchanged); README, CHANGELOG and research corrected (v0.1.0's re-verification, reproducibility, not measured, fallback triggers, the update's commit); decision records 0003 and 0004

---

## Phase 4: Release and adoption

- [X] T014 `preset.yml` 0.2.0, `CHANGELOG.md` 0.2.0 (Changed: the Resume rule; the eval), README status and install URL, `CLAUDE.md`'s version mention
- [X] T015 `/speckit-converge` until a pass finds nothing above LOW
- [ ] T016 Fresh review of the whole PR; **the owner reviews against constitution I–V**; on approval, mark ready, `gh pr merge --auto --squash` on green, tag `v0.2.0`, and install from the tag in a scratch repository
- [ ] T017 Dotfiles: `sdd-init`'s story-workers URL to `v0.2.0` (the check pins the shape, so no red is owed for a version move), `./check.sh`, a real `sdd-init` in a scratch repository, PR draft → fresh review → ready → merge on green
- [ ] T018 supertrader: on `main`, `specify preset update story-workers --from <v0.2.0>` in a worktree, a fresh-context review (its governance), commit; then merge `main` into `001-truthful-market-simulation` with the owner's uncommitted work untouched (git refuses on overlap)

## Dependencies

Phase 1 → Phase 2 → Phase 3 (the run needs the fragment) → Phase 4. T012 waits for the owner's
confirmation; T016 for the owner's review.

## Phase 5: Convergence

- [X] T026 Run a fresh `with` arm and a fresh `--preset v0.1.0` arm on `checkout` and record them in Eval 003, or record the owner's acceptance of the unmeasured fresh path beside README's "Not measured", linked from CHANGELOG 0.2.0, per Constitution III (partial)
- [X] T027 Bring 001 spec FR-006/FR-007 and contracts/fragment.md §6/§9 to 0.2.0's hand-off exception, the main session's own commits and the dirty-tree fallback trigger per T021/T022 docs-to-match (partial)
- [X] T028 Add compose phrases for "name those paths in the completion report" and "say so in the completion report in place of the line below", each seen red, per FR-007 (partial)
- [X] T029 Reconcile US1/AC5, the second-session clarification and decision 0003 with FR-005's "when a phase went to a worker" per US1/AC5 (contradicts)
- [X] T030 Test the state-chain depth refusal (deeper than 5, and a cycle) in test_run.py and test_resume_check.py, seen red, per contracts/harness.md (partial)
- [X] T031 Update plan.md's Testing spend line to four runs and $9.52 per plan: Technical Context (partial)
- [X] T032 Bold the "A clean tree outside the feature" cross-reference in the fragment's Hand-offs per Constitution I wording (partial)

## Phase 6: Convergence

- [X] T033 Align US2's Independent Test and FR-008's list of runs with the two fresh runs recorded in Eval 003 per US2 Independent Test (contradicts)
- [X] T034 Update plan.md (Summary, Technical Context Testing, Scale/Scope) and quickstart.md (spend, pass conditions incl. fresh-1) to the six runs and $14.61 of spent.txt per plan: Technical Context (partial)
- [X] T035 Qualify research R1's "always carries `Started at phase <n>:`" with "when a phase went to a worker" per FR-005 (contradicts)
- [X] T036 Add "0.2.0: none when the phase marked nothing new" to 001 spec FR-004's `tasks: mark phase <n>` per FR-006 (partial)
