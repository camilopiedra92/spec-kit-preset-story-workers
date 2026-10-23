---

description: "Task list for 004-fragment-form-and-observation"
---

# Tasks: Fragment form, and observed verification

**Input**: `specs/004-fragment-form-and-observation/` (spec, plan, research)

**Tests**: requested for logic of its own (`fragment_rules.py`, the stand-in, `--no-git`, the two
checks). Tests first, each seen red for its predicted reason. `tests/check.sh` once per story close,
not before every commit. The feature's fresh-context pass is the owner's.

## Phase 1: Spec (PR 1, draft)

- [X] T001 Inventory (R1 to R88), justification sentences (J1 to J6), new rules (N1 to N5), mapping, research, ADR 0005 superseded, CHANGELOG correction
- [X] T002 Eval budget confirmed in the spec (owner approved model usage, 2026-10-23)

## Phase 2: Harness for E3 and E2 (PR 2, draft)

- [X] T003 `test_run.py`: `--no-git` cases, red first (flag unknown); then `run.sh --no-git`
- [X] T004 `test_nogit_check.py` red, then `nogit_check.py`; break each check by hand
- [X] T005 `test_observe_check.py` red, then `observe_check.py`; break each check by hand
- [X] T006 `tests/check.sh`

## Phase 3: US1, the form (PR 3, draft)

- [X] T007 `tests/fragment_rules.py` and its `compose.sh` call and red checks (bullet removed, duplicated, inventory row dropped); migrated phrases; run against the current fragment: red, each for its reason
- [X] T008 Rewrite `commands/speckit.implement.md` to the mapping; T007 green; `core-anchors.sh` green
- [X] T009 README "Why the fragment's rules read as they do" (J1 to J6, unmeasured); CHANGELOG `[Unreleased]`
- [X] T010 Hand-break: a bullet removed, one duplicated, one reworded in the fragment: red each
- [ ] T011 `tests/check.sh`; story close; fresh review (owner)

## Phase 4: US2, observation (PR 4, draft)

- [X] T012 `compose.sh`: phrases for N1 to N5 and the git stand-in, red first (rules absent); hand-break each command
- [X] T013 Add the Observation section (N1 to N5); mapping rows `N` in plan.md; `fragment_rules.py` accepts them
- [X] T014 README and CHANGELOG (new rule, unmeasured)
- [ ] T015 `tests/check.sh`; story close; fresh review (owner)

## Phase 5: Evals (PR 5, draft)

- [ ] T016 Probes; E1, E2, E3 on the harness, three counted runs per arm
- [ ] T017 Judge with `resume_check.py`, `observe_check.py`, `nogit_check.py`; record in the README as they came out; update the spec's Status; CHANGELOG links
