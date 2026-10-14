# Feature Specification: Story workers

**Feature Branch**: `001-story-workers`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Have /speckit-implement hand each phase of a feature's tasks to a
worker subagent on a smaller model, while the main session verifies, reviews and decides; ship it
only if a measurement shows it saves usage without losing quality." (shaped in a conversation of
2026-10-13; first specified against the archived test-first preset, whose ledger-specific parts
are dropped here)

## Context

Core `/speckit-implement` runs every task in the main session, on whatever model that session uses.
Most of a feature's tokens are spent there — reading code, writing tests and code, running the
suite — while the judgement-heavy steps (the spec, the plan, the tasks, verification, review) are
short. On the largest model that is where a subscription's usage goes. Core already executes "phase
by phase" and asks to "verify each phase completion before proceeding": the phase is the natural
unit to hand over.

A lead model that plans and checks while a smaller model executes is the pattern Anthropic
describes for its own multi-agent research system (Opus lead, Sonnet subagents; "How we built our
multi-agent research system", Anthropic engineering, 2025).

Observed on 2026-10-13 (Claude Code 2.1.296, git 2.56.0; `claude -p` in scratch repositories; one
run each; research.md R1):

- A subagent started with `model: "sonnet"` on the Agent call ran on `claude-sonnet-5-5`, the main
  session on `claude-opus-5-5`; nothing was installed for it.
- The subagent had the project's `CLAUDE.md` and the user's global instructions in its context
  without reading any file: a worker follows the project's own rules as the main session does.
- The project's hooks fired for the subagent's tool calls, and a hook's exit-2 message reached it.
- An Agent call without `model` ran on the main session's model, unless `CLAUDE_CODE_SUBAGENT_MODEL`
  was set (then on that model); a `model` on the call won over the variable.

What the observations do not settle, and the release must measure (constitution III): whether a
feature implemented with workers uses less usage than without them, once the main session's
verification is counted, and whether it delivers code that is any worse.

## Clarifications

### Session 2026-10-13

- Q: What usage cut justifies shipping? → A: 30%, counting the main session's verification and any
  review.
- Q: What feature is measured? → A: a synthetic two-story feature committed as a fixture, so the
  measurement can be rerun on a later version.
- Q: How many runs per arm? → A: one per arm, reported as directional.
- Q: Who applies a fix that verification or a review finds? → A: a worker briefed with it; the main
  session verifies again.
- Q: If the measurement fails, what happens to the branch? → A: only the README entry reaches
  `main`, recording the rule as measured and not adopted; the branch stays unmerged under a tag so
  it can be rerun.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A phase's tasks run in a worker (Priority: P1)

A developer runs `/speckit-implement` in a project with this preset installed. For each phase of
`tasks.md`, in order, the main session hands the phase's tasks to a worker on the smaller model.
The worker carries them out under core's execution rules and the project's own instructions, and
returns a report. The main session then verifies the phase in its own runs, marks what passes, and
sends anything to fix back to a worker. Any review the project's instructions call for runs in a
fresh context on the main session's model, never in a worker.

**Why this priority**: it is the feature; without it nothing moves off the larger model.

**Independent Test**: the worker arm of the measurement (User Story 2) is this story's end-to-end
test: in its stream, the main session's file edits touch only `tasks.md` (SC-003), the workers'
turns ran on the smaller model, and each `[X]` follows a whole-suite run by the main session.

**Acceptance Scenarios**:

1. **Given** a feature with a setup phase and two user stories, **When** `/speckit-implement` runs,
   **Then** each phase is carried out by its own worker, one after another, never two at once.
2. **Given** a worker that reports its phase done, **When** the main session's own run of the suite
   or of the project's static checks fails, **Then** no task of the phase is marked done, and the
   failure goes to a worker briefed with it.
3. **Given** a worker whose commits touch files outside its phase's tasks, **When** the main session
   verifies, **Then** those changes are sent back to a worker or reported, and nothing is marked
   until they are resolved.
4. **Given** a project whose instructions call for a review per story, **When** a story's phase is
   verified, **Then** the reviewer is started in a fresh context with the main session's model named
   on the call, and each finding it proves goes to a worker, then verification again.
5. **Given** a worker that returns with some tasks unfinished, **When** the main session has verified
   the rest, **Then** one new worker gets the unfinished tasks, briefed with what is done; if it too
   makes no progress, the main session stops and reports.
6. **Given** an agent that cannot start a subagent on a named model, **When** `/speckit-implement`
   runs, **Then** the main session carries out the tasks itself exactly as core does, and says so in
   the completion report.

---

### User Story 2 - The release carries its measurement (Priority: P2)

The owner deciding whether to release reads, in the README, a measured comparison on a committed
fixture: the same two-story feature implemented with the preset and without it, each arm's usage per
model and in total, and each arm's result on acceptance tests the agent never saw, with the version
of every tool involved. A later version reruns the same fixture.

**Why this priority**: constitution III makes it the condition of release, and it is the only answer
to whether the preset pays for itself.

**Independent Test**: the README entry names the fixture and its size, the arms, the runs per arm,
each arm's usage per model and in total, each arm's held-out test results, and the versions of Spec
Kit, Claude Code, the model IDs, git and the test runner.

**Acceptance Scenarios**:

1. **Given** both arms run, **When** SC-001 and SC-002 hold, **Then** the README records the result
   and the preset is released.
2. **Given** both arms run, **When** either fails, **Then** the preset is not released; the README
   entry alone reaches `main`, recording the rule as measured and not adopted with the reason, and
   the branch is tagged and left unmerged.

### Edge Cases

- **A worker ends with the suite red**: verification catches it (FR-004); a Stop hook a project
  has fires at the end of the main session's turn, not at a subagent's.
- **No worker can be started**: the session has no Agent tool, or the Agent call errors before the
  worker's first tool call (FR-007).
- **A worker fails mid-phase** (an error, no report): treated as unfinished tasks (FR-006); when the
  error is a usage limit, the main session stops and reports rather than continuing on the larger
  model.
- **A run resumes** after an interruption and finds a phase with commits but unmarked tasks: it
  verifies them as FR-004 says, marks what passes, and hands the rest to a worker.
- **`[P]` tasks**: they run inside one phase's worker, one after another; parallel workers would
  write the same worktree at once.
- **`CLAUDE_CODE_SUBAGENT_MODEL` is set**: the worker still runs on the smaller model and the
  reviewer on the main session's, because both calls name their model.
- **The main session is already on the smaller model**: the hand-off still happens; not measured.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fragment MUST hand each phase of `tasks.md` to one worker, in the order core runs
  them, with no two workers active at once.
- **FR-002**: The worker MUST be started with `model: "sonnet"` on the call, the family alias, so a
  newer model of the family is picked up without a release.
- **FR-003**: The worker's brief MUST point it at core's execution rules in the composed skill rather
  than repeating them, and MUST carry the phase's tasks, the feature directory, the commands the
  project names for its suite and static checks, and what earlier workers finished; the worker MUST
  NOT mark a checkbox, start a review, or start another worker.
- **FR-004**: The main session MUST mark a task `[X]` only after, in its own runs, the whole suite
  passes, the project's static checks report nothing new, and the phase's commits change nothing
  outside the phase's tasks and `tasks.md`'s own entries for them. A worker's report never marks a
  task.
- **FR-005**: Any review the project's instructions or a command call for MUST be started in a fresh
  context with `model` set to the main session's own model, and never run by a worker.
- **FR-006**: Unfinished tasks — after verification, a worker's error or missing report included —
  MUST go to one new worker briefed with what is done; if it makes no progress, the main session
  stops and reports. Every fix that verification or a review finds MUST go to a worker briefed with
  it, then verification again. The main session writes no code itself, except under FR-007.
- **FR-007**: When no worker can be started (Edge Cases), the main session MUST carry out the tasks
  as core does and say so in the completion report (constitution IV).
- **FR-008**: The fragment MUST name each core rule it narrows — "For completed tasks, make sure to
  mark the task off as [X]" and "parallel tasks [P] can run together" — and the composition test MUST
  fail when core no longer carries one (constitution I).
- **FR-009**: The README MUST record the measurement of User Story 2 with the fixture's size, that
  one synthetic feature is less representative than a real one, and that a change in Claude Code
  breaking the observations of Context shows only in a rerun of the measurement.
- **FR-010**: The fixture, its held-out tests and the harness MUST live under `tests/`, outside the
  release archive (constitution V), with the steps to rerun both arms.

### Key Entities

- **Worker**: a subagent started for one phase with `model: "sonnet"` on the call.
- **Phase hand-off**: the phase's tasks, the feature directory, the suite and static-check commands,
  what earlier workers finished, the pointer to core's execution rules and what the worker must not
  do; for a fix, the finding itself.
- **Worker report**: the tasks done and not done, anything it found that no task covers, and the
  output of its last whole-suite run.
- **Measurement**: per arm, usage per model and in total from the run's own accounting, the held-out
  test results, the stream, and the tool versions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fixture, the worker arm's total usage — every model's, the main session's
  verification and any review included — is at least 30% lower than the arm without the preset.
- **SC-002**: On the fixture, the worker arm passes at least as many of the held-out acceptance
  tests as the arm without the preset, and its own suite is green at the end.
- **SC-003**: In the worker arm's stream, every Write, Edit or NotebookEdit call the main session
  makes targets the feature's `tasks.md`; its shell commands are listed beside the result, for a
  reviewer to confirm none writes code.
- **SC-004**: The composition test goes red when either core rule FR-008 names is removed, seen red
  once before it is trusted.

## Assumptions

- Nothing is installed in a project for the worker (research.md R1).
- The measurement holds for a main session on Opus at its default effort; on another model or
  effort it is not measured, and the README says so.
- Usage is compared by the per-model cost Claude Code reports for a headless run (list price,
  subagents included), since a subscription's window is not exposed per run.
- Held-out acceptance tests, written with the fixture and never copied into the run, judge both arms
  the same way; the agent's own tests differ between arms and are not compared.
- Effort is not set for the worker or the reviewer; each model's default applies.
- Agents other than Claude Code fall back to core (FR-007).
