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
The hypothesis this feature tests is that most of a feature's usage is spent there — reading code,
writing tests and code, running the suite — while the steps that need the larger model's judgement
(the spec, the plan, the tasks, verification, review) are short. Core already executes "phase by
phase" and asks to "verify each phase completion before proceeding": the phase is the natural unit
to hand over.

A lead model that plans and checks while a smaller model executes is the pattern Anthropic
describes for its own multi-agent research system (Opus lead, Sonnet subagents; "How we built our
multi-agent research system", Anthropic engineering, 2025).

Observed on 2026-10-13 with Claude Code 2.1.296 (research.md R1 lists each run): a subagent started
with `model` and `effort` on the Agent call runs with them, whatever the main session's; without
them it takes the main session's model and effort (or `CLAUDE_CODE_SUBAGENT_MODEL`'s model when
set); it has the project's `CLAUDE.md` in its context; the project's hooks apply to its calls; a
project agent named `general-purpose` replaces the built-in one's prompt but not the call's model.

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
  `main`, recording the rule as measured and not adopted; the branch stays unmerged under a tag.
- Q: Does the worker inherit the main session's effort? → A: no: the worker's call sets
  `effort: "medium"`, so raising the main session's effort for planning does not raise every
  worker's; a review inherits the main session's. Recorded as an exception to the owner's policy of
  leaving effort at each model's default, with its reason (research.md R7).
- Q: Does the eval run with the owner's own configuration? → A: no: it runs hermetic — the user's
  instructions, settings, hooks, skills, plugins and MCP servers excluded, the project's kept — so
  the result depends on the preset and Claude Code's version and anyone can reproduce it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A phase's tasks run in a worker (Priority: P1)

A developer runs `/speckit-implement` in a project with this preset installed. For each phase of
`tasks.md`, in order, the main session hands the phase's tasks to a worker on the smaller model.
The worker carries them out under core's execution rules and the project's own instructions,
commits its work, and returns a report. The main session verifies the phase in its own runs, marks
what passes, and sends anything to fix back to a worker. Any review the project's instructions call
for runs in a fresh context on the main session's model, never in a worker.

**Why this priority**: it is the feature; without it nothing moves off the larger model.

**Independent Test**: the `with` arm of the eval (User Story 2) is this story's end-to-end test: in
its stream the main session edits only `tasks.md` (SC-003), the workers' turns ran on the smaller
model, every worker commit follows the fixture's commit-message rule (so the project's instructions
reached the worker), and each `[X]` follows a whole-suite run by the main session.

**Acceptance Scenarios**:

1. **Given** a feature with a setup phase and two user stories, **When** `/speckit-implement` runs,
   **Then** each phase is carried out by its own worker, the next only after the previous one's
   verification, never two at once.
2. **Given** a worker that reports its phase done, **When** the main session's own run of the suite
   fails or the static checks report something the baseline did not, **Then** no task of the phase
   is marked done, and the failure goes to a worker briefed with it.
3. **Given** a worker whose commits touch files outside its phase's tasks, **When** the main session
   verifies, **Then** those changes go back to a worker or into the report, and nothing is marked
   until they are resolved.
4. **Given** a project whose instructions call for a review per story, **When** a story's phase is
   verified, **Then** the reviewer is started in a fresh context with the main session's model
   family named on the call, and each finding it proves goes to a worker, then verification again.
5. **Given** a hand-off that comes back with nothing it was given resolved, **When** the main
   session has verified it, **Then** one new worker gets what remains; a second such hand-off stops
   the run with a report.
6. **Given** a session with no Agent tool, or whose first Agent call returns an error and no report
   for a reason other than a usage limit, **When** `/speckit-implement` runs, **Then** the main
   session carries out the tasks itself as core does, and says so in the completion report.

---

### User Story 2 - The release carries its measurement (Priority: P2)

The owner deciding whether to release reads, in the README, a measured comparison on a committed
fixture, run hermetically: the same two-story feature implemented without the preset, with it, and
with it but no Agent tool (the fallback), each arm's usage per model and in total, and its result on
acceptance tests the agent never saw, with the date and the version of every tool and model.

**Why this priority**: constitution III makes it the condition of release, and constitution IV asks
its fallback to be evaluated where the capability can be withheld.

**Independent Test**: the README entry names the fixture and its size (stories, tasks, held-out
tests), the date, the arms, the runs per arm, each arm's usage per model and in total, each arm's
held-out results, the isolation used, and the versions of Spec Kit, Claude Code, the model IDs,
git, uv, Python and pytest.

**Acceptance Scenarios**:

1. **Given** all three arms run and count (FR-011), **When** SC-001, SC-002 and SC-005 hold,
   **Then** the README records the result and the preset is released.
2. **Given** all three arms run, **When** any of them fails, **Then** the preset is not released;
   the README entry alone reaches `main`, recording the rule as measured and not adopted with the
   reason, and the branch is tagged and left unmerged.

### Edge Cases

- **A worker ends with the suite red**: verification catches it (FR-004); a project's Stop hook
  fires at the end of the main session's turn, not at a subagent's.
- **A worker's error is a usage limit**, at any point: the main session stops and reports; it never
  continues the tasks itself on the larger model.
- **A project hook blocks a worker's call**: the worker follows the hook's message, or leaves the
  task unfinished with the message in its report; the main session never makes the blocked call
  itself.
- **A run resumes** after an interruption: a phase with commits but unmarked tasks is verified as
  FR-004 says; uncommitted changes go to a worker briefed with the diff, to finish or discard, then
  verification.
- **The project names no suite or static check**: the main session verifies with what it has, says
  in the completion report what was missing, and otherwise marks as core does.
- **`[P]` tasks** run inside their phase's worker, one after another: two workers would write the
  same worktree and index at once.
- **`CLAUDE_CODE_SUBAGENT_MODEL` is set**: the worker still runs on the smaller model and the
  reviewer on the main session's family, because both calls name their model.
- **The project defines its own `general-purpose` agent**: it is used as the worker, with its own
  prompt; the call's model and effort still apply (observed, R1).
- **The main session is already on the smaller model**: the hand-off still happens; not measured.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fragment MUST hand each phase of `tasks.md` to one worker, in the order core runs
  them, the next only after the previous one's verification, with no two workers active at once.
- **FR-002**: The worker MUST be started with `model: "sonnet"` (the family alias, so a newer model
  of the family is picked up without a release) and `effort: "medium"` on the call.
- **FR-003**: The worker's brief MUST point it at core's "Project Setup Verification" (first phase
  only), "Execute implementation", "Implementation execution rules" and "Progress tracking and error
  handling" steps in the composed skill rather than repeating them, and MUST carry the phase's tasks,
  the feature directory, the suite and static-check commands — from the project's instructions, else
  `plan.md`'s Technical Context — what earlier workers finished, and, for a fix, the finding itself.
  The worker MUST commit its work, one commit per task, and MUST NOT edit `tasks.md`, start a review
  or start another worker.
- **FR-004**: The main session MUST mark a task `[X]` only after, in its own runs, the whole suite
  passes, the static checks report nothing beyond the baseline it ran before the phase's worker
  started, and the phase's commits — those between the HEAD it recorded before the phase's first
  worker and HEAD after verification — change only files a task of the phase names, or files in a
  directory one names; uncommitted changes count as outside. A worker's report never marks a task.
- **FR-005**: Any review the project's instructions or a command call for MUST be started in a fresh
  context with `model` set to the main session's model family and no `effort`, so it inherits the
  main session's, and never run by a worker.
- **FR-006**: A hand-off — unfinished tasks, a failed verification, a review finding — MUST go to a
  worker briefed with it, then verification again. A hand-off resolves nothing when, after
  verification, none of what it was given passes; the main session then gives what remains to one
  new worker, and stops and reports at the second such hand-off. The main session's only file
  writes are `tasks.md` — its checkboxes and any task a worker reported finding — and its commit of
  them, except under FR-007.
- **FR-007**: When no worker can be started (US1 scenario 6), the main session MUST carry out the
  tasks as core does and say so in the completion report (constitution IV).
- **FR-008**: The fragment MUST name each core rule it narrows — "For completed tasks, make sure to
  mark the task off as [X]" and "parallel tasks [P] can run together" — and the composition test
  MUST fail when core no longer carries one, or no longer has a step the brief points at
  (constitution I).
- **FR-009**: The README MUST record the eval of User Story 2 with everything its Independent Test
  lists, that one synthetic feature is less representative than a real one, and where a break of
  each Context observation would show: a per-call model or effort break in the arm's usage per
  model, instructions no longer reaching the worker in the fixture's commit-message check.
- **FR-010**: The fixture, its held-out tests and the harness MUST live under `tests/`, outside the
  release archive (constitution V), with the steps to rerun every arm.
- **FR-011**: An eval arm MUST count only when the agent exited 0 within its deadline and its result
  reports no error; otherwise the harness records it as failed and writes no usage or held-out
  result for it.

### Key Entities

- **Worker**: a subagent started for one hand-off with `model: "sonnet"` and `effort: "medium"`.
- **Hand-off**: the phase's tasks (or the fix's finding), the feature directory, the suite and
  static-check commands, what earlier workers finished, the pointer to core's steps, and what the
  worker must not do.
- **Worker report**: the commits it made (first and last), the tasks done and, for each not done,
  what stopped it, anything it found that no task covers, and the output of its last whole-suite
  run.
- **Eval arm**: `without` (no preset), `with`, `fallback` (`with`, no Agent tool); per arm, usage per
  model and in total, held-out results, the suite, the stream, the status, and the versions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fixture, the `with` arm's total usage — every model's, the main session's
  verification and any review included — is at least 30% lower than the `without` arm's.
- **SC-002**: On the fixture, the `with` arm passes at least as many held-out acceptance tests as
  `without`, and its own suite is green at the end.
- **SC-003**: In the `with` arm's stream, every Write, Edit or NotebookEdit call the main session
  makes targets the feature's `tasks.md`; its shell commands are listed beside the result, for a
  reviewer to confirm none writes code.
- **SC-004**: The composition test goes red when a core rule FR-008 names, or a core step the brief
  points at, is removed, seen red once before it is trusted.
- **SC-005**: The `fallback` arm passes at least as many held-out tests as `without`, ran on no
  model but the main session's, and its completion report says the tasks ran in the session.

## Assumptions

- Nothing is installed in a project for the worker (research.md R1).
- The eval pins the main session to Opus at `--effort medium`, its default today; another model or
  effort is not measured, and the README says so.
- Usage is compared by the per-model cost Claude Code reports for a headless run (list price,
  subagents included), since a subscription's window is not exposed per run.
- Held-out acceptance tests — at least one per acceptance scenario of the fixture's spec, against
  the interface its plan fixes — judge every arm by the same oracle; the agent's own tests differ
  between arms and are not compared.
- The hermetic eval leaves in what no flag removes: admin-managed settings and Claude Code's
  built-in skills and plugins; the harness records which loaded.
- Agents other than Claude Code fall back to core (FR-007).
