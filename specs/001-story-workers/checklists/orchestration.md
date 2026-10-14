# Orchestration Checklist: Story workers

**Purpose**: Requirements quality of the hand-off, verification, fallback and eval, before `/speckit-tasks`
**Created**: 2026-10-13
**Feature**: [spec.md](../spec.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.

Depth: standard. Audience: the pull request's reviewer. Focus: the hand-off and verification
contract, and the validity of the eval.

## Requirement Completeness

- [x] CHK001 Are all items the brief carries listed identically in the spec, the contract and the Key Entities? [Consistency, Spec §FR-003, Contract §3]
- [x] CHK002 Is the worker report specified completely enough for the main session to verify and report without asking the worker again? [Completeness, Spec §Key Entities, Contract §4]
- [x] CHK003 Is the worker's handling of `tasks.md` defined: what it may edit (if anything) and what it may not (checkboxes)? [Gap, Spec §FR-003]
- [x] CHK004 Is where the project's "suite and static-check commands" come from defined, and what happens when a project names none? [Gap, Spec §FR-003, §FR-004]
- [x] CHK005 Are the setup, foundational and polish phases covered by the same rule as story phases? [Coverage, Spec §FR-001]

## Requirement Clarity

- [x] CHK006 Is "makes no progress" defined by an observable condition? [Ambiguity, Spec §FR-006]
- [x] CHK007 Is "no worker can be started" defined by conditions the main session can check? [Clarity, Spec §Edge Cases, §FR-007]
- [x] CHK008 Is "the static checks report nothing new" anchored to a baseline that is defined, and when it is taken? [Ambiguity, Spec §FR-004]
- [x] CHK009 Is "changes nothing outside the phase's tasks" decidable from the commits and `tasks.md` alone? [Measurability, Spec §FR-004]

## Requirement Consistency

- [x] CHK010 Does FR-004's marking rule agree with core's "**Validation checkpoints**: Verify each phase completion before proceeding"? [Consistency, Spec §FR-004]
- [ ] CHK011 Is "The main session writes no code itself" consistent with the main session editing `tasks.md`, committing, and installing anything a project's own instructions require? [Consistency, Spec §FR-006, §SC-003]
- [x] CHK012 Is the review rule (FR-005) consistent with a project whose instructions call for no review at all? [Consistency, Spec §FR-005, Constitution IV]

## Acceptance Criteria Quality

- [x] CHK013 Is SC-001's usage computable the same way twice from the same outputs? [Measurability, Spec §SC-001, Research §R6]
- [x] CHK014 Are the held-out tests' independence from both arms and their size specified? [Completeness, Spec §SC-002, Research §R6]
- [x] CHK015 Is SC-003 checkable from the stream alone, and are its known blind spots (shell writes) stated? [Measurability, Spec §SC-003]
- [x] CHK016 Is the decision when only one of SC-001 and SC-002 holds stated? [Completeness, Spec §US2]

## Scenario Coverage

- [x] CHK017 Is a worker that returns an error, no report, or hits a usage limit addressed? [Coverage, Spec §Edge Cases, §FR-006]
- [x] CHK018 Is a project hook that blocks a worker's call (exit 2) addressed? [Gap, Research §R1]
- [x] CHK019 Is resumption after an interrupted run specified? [Coverage, Spec §Edge Cases]
- [x] CHK020 Is the case of a project already using a different subagent setup (its own agents, `CLAUDE_CODE_SUBAGENT_MODEL`) addressed? [Coverage, Spec §Edge Cases]

## Eval Validity

- [x] CHK021 Do the arms differ only in the preset: same fixture, pinned main model, same tool versions recorded? [Completeness, Research §R6, Contract run.sh]
- [x] CHK022 Is the fixture's size and its representativeness limit stated where the README reader sees it? [Completeness, Spec §FR-009]
- [x] CHK023 Is a run that fails partway (deadline, crash) handled so it cannot be mistaken for a result? [Gap, Contract run.sh]
- [x] CHK024 Is the tool permission set for the headless run the same for both arms and sufficient for implement? [Gap, Contract run.sh]

## Dependencies & Assumptions

- [x] CHK025 Is the dependency on Claude Code behaviour (per-call model, CLAUDE.md in subagents) recorded with its version and where a break would show? [Dependency, Research §R1, Spec §FR-009]
- [x] CHK026 Is the main session's model and effort recorded as an assumption of the measurement? [Assumption, Spec §Assumptions]
