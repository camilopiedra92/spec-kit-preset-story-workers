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
(the spec, the plan, the tasks, verification, review) are short. Core already runs "Phase-by-phase
execution" and asks to "Verify each phase completion before proceeding": the phase is the natural
unit to hand over.

A lead model that plans and checks while a smaller model executes is the pattern Anthropic
describes for its own multi-agent research system (Opus lead, Sonnet subagents; "How we built our
multi-agent research system", Anthropic engineering, 2025).

Observed on 2026-10-13 with Claude Code 2.1.296 (research.md R1 lists each run): a subagent started
with `model` and `effort` on the Agent call runs with them, whatever the main session's, even when
the project defines its own `general-purpose` agent; without them it takes the main session's
model and effort, or `CLAUDE_CODE_SUBAGENT_MODEL`'s model when that is set. It has the project's
`CLAUDE.md` in its context, the project's hooks apply to its calls and their messages reach it, and
a project's `Stop` hook fires once, at the end of the main session's turn, not when a subagent stops.

What the observations do not settle, and the release must measure (constitution III): whether a
feature implemented with workers uses less usage than without them, once the main session's
verification is counted, and whether it delivers code that is any worse.

## Clarifications

### Session 2026-10-13

- Q: What usage cut justifies shipping? → A: 30%, counting the main session's verification and any
  review.
- Q: What feature is measured? → A: a synthetic two-story feature committed as a fixture, so the
  measurement can be rerun on a later version.
- Q: How many runs per arm? → A: one counted run per arm, reported as directional.
- Q: Who applies a fix that verification or a review finds? → A: a worker briefed with it; the main
  session verifies again.
- Q: If the measurement fails, what happens to the branch? → A: the branch merges to `main` with
  the README recording the rule as measured and not adopted, and no release: `preset.yml` keeps a
  pre-release version and no version tag is made, so nothing is installable (projects install from
  a tag). The measured state is also tagged `measured-not-adopted-<date>`. Amended 2026-10-14 from
  "only the README reaches `main`, the branch unmerged": the ruleset requires `compose (pinned)` on
  every pull request to `main`, which a README-only change cannot produce, and the owner chose a
  follow-up feature that builds on this harness.
- Q: Does the worker inherit the main session's effort? → A: no: the worker's call sets
  `effort: "medium"`, so raising the main session's effort for planning does not raise every
  worker's; a review inherits the main session's. Recorded as an exception to the owner's policy of
  leaving effort at each model's default, with its reason (research.md R7).
- Q: Does the eval run with the owner's own configuration? → A: no: hermetic — the user's
  instructions, settings, hooks, skills, plugins and MCP servers excluded, the project's kept — so the
  result depends on the preset and Claude Code's version, and anyone can reproduce it.
- Q: What happens when a worker cannot go on — a usage limit, an error, no report? → A: the main
  session carries out the remaining tasks as core does and says why in the completion report
  (constitution IV): never worse than without the preset.
- Q: An eval arm that does not count (a crash, the deadline, an error)? → A: it is not a
  measurement: rerun, up to twice; only counted arms that miss a criterion are recorded as not
  adopted.
- Q: Does the fixture call for a review per story? → A: yes, in its `CLAUDE.md`, as a
  `general-purpose` subagent so the stream can tell it from other subagents, so the measured
  usage includes the reviews the owner's own setup asks for (decided on the owner's standing
  instruction to take the recommended option).
- Q: What bounds fix hand-offs that keep breaking each other? → A: at most two fix hand-offs per
  phase, whatever items they carry; after that the phase's remaining items run as core does
  (same standing instruction).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A phase's tasks run in a worker (Priority: P1)

A developer runs `/speckit-implement` in a project with this preset installed. For each phase of
`tasks.md`, in order, the main session hands the phase's tasks to a worker on the smaller model. The
worker carries them out under core's execution rules and the project's own instructions, commits
each task, and returns a report. The main session verifies the phase in its own runs, reads its
diff, marks what passes, and sends anything to fix back to a worker. Any review the project's
instructions call for runs in a fresh context on the main session's model, never in a worker.

**Why this priority**: it is the feature; without it nothing moves off the larger model.

**Independent Test**: the `with` arm of the eval (User Story 2) is this story's end-to-end test: in
its stream the main session edits no tracked file but `tasks.md` (SC-003), the workers' turns ran on
the smaller model, one phase at a time with a worker for each, the fixture's commit-message rule holds on every code commit (so the project's
instructions reached the workers), and each story's review ran on the main session's model
(SC-007); that each `[X]` follows a whole-suite run by the main session is read from the stream by
the reviewer of the eval, not checked by a tool.

**Acceptance Scenarios**:

1. **Given** a feature with a setup phase and two user stories, **When** `/speckit-implement` runs,
   **Then** each phase is carried out by its own worker, the next only after the previous one's
   verification, never two at once.
2. **Given** a worker that reports its phase done, **When** the main session's own run of the suite
   fails, or of the static checks reports a finding its baseline did not have, **Then** no task of
   the phase is marked done, and the failure goes to a worker briefed with it.
3. **Given** a phase whose diff changes files no task of the phase calls for, **When** the main
   session reads it, **Then** those changes go back to a worker, and nothing is marked until a
   reading of the diff finds them resolved.
4. **Given** a project whose instructions call for a review per story, **When** a story's phase is
   verified, **Then** the reviewer is started in a fresh context with the main session's model
   family named on the call, and each finding it proves goes to a worker, then verification again.
5. **Given** a phase that has had two fix hand-offs, **When** verification still fails, **Then** the
   main session carries out the phase's remaining items itself as core does, and says so in the
   completion report.
6. **Given** a session with no Agent tool, or a worker that returns an error or no report, **When**
   it happens, **Then** the main session carries out the remaining tasks itself as core does, and
   says why in the completion report.

---

### User Story 2 - The release carries its measurement (Priority: P2)

The owner deciding whether to release reads, in the README, a measured comparison on a committed
fixture, run hermetically: the same two-story feature implemented without the preset, with it, and
with it but no Agent tool (the fallback), each arm's usage per model and in total and its result on
acceptance tests the agent never saw, with the date and the version of every tool and model. The
same harness reruns the observations the design rests on, so a Claude Code release that breaks one
shows up as a failed probe.

**Why this priority**: constitution III makes it the condition of release, and constitution IV asks
for the fallback to be evaluated where the capability can be withheld.

**Independent Test**: the README entry names the fixture and its size (stories, tasks, held-out
tests), the date, the arms, the counted runs per arm and any rerun with its reason, each arm's usage
per model and in total, each arm's held-out results, the isolation used, the probes' results, and
the versions of Spec Kit, Claude Code, the model IDs and efforts, git, uv, Python, pytest and ruff.

**Acceptance Scenarios**:

1. **Given** all three arms counted, **When** every success criterion SC-001 to SC-007 holds,
   **Then** the README records the result and the preset is released.
2. **Given** all three arms counted, **When** any success criterion does not hold, **Then**
   the preset is not released: the branch merges with the README recording the rule as measured
   and not adopted with the reason, no version tag is made, and the measured state is tagged
   `measured-not-adopted-<date>` (Clarifications).
3. **Given** an arm that does not count, **When** it is rerun twice without counting, **Then** no
   result is recorded and the reason is reported to the owner.

---

### User Story 3 - The owner's setup adopts the released preset (Priority: P3)

Once the preset is released, every repository the owner starts with Spec Kit gets it, the projects
already on Spec Kit can take it, and the owner's documented policies stay true.

**Why this priority**: without it the release reaches no project; it only follows a pass of User
Story 2.

**Independent Test**: `sdd-init` in a scratch repository installs both presets; the dotfiles check
for `sdd-init` goes red when the story-workers preset is removed from it; `docs/claude-settings.md`
names the exception; each existing Spec Kit project the owner approves has the preset in a commit of
its own.

**Acceptance Scenarios**:

1. **Given** the released tag, **When** `sdd-init` runs in a new repository, **Then** it installs
   `constitution-authoring` and `story-workers` in its one commit.
2. **Given** dotfiles' effort policy, **When** the preset is released, **Then** the policy names the
   worker's effort as its one exception and links the decision record.
3. **Given** a project already on Spec Kit, **When** the owner approves it, **Then** it gets
   `specify preset add` of the tag in a commit of its own, and no other change.

### Edge Cases

- **A worker ends with the suite red**: verification catches it (FR-004); a project's Stop hook
  fires at the end of the main session's turn, not at a subagent's (observed, R1).
- **A project hook blocks a worker's call**: the worker receives the hook's message (observed) and
  follows it or leaves the task unfinished with the message in its report; the main session never
  makes the blocked call itself, also under FR-007: such a task stays unfinished and goes into the
  completion report.
- **A run resumes** (rule of 0.2.0, feature 003): every run starts at the first phase with a task
  not marked `[X]` or `[x]`, skipping all-marked phases; each phase's baseline is taken as
  Verification says; the worker gets only the unmarked tasks and checks what the repository already
  holds; a run that finds uncommitted changes outside the feature directory is
  carried out as core does; the main session commits what it carries out outside it; the completion report says where the
  run started and that work committed before it had the suite but no diff reading.
  (0.1.0 resumed after the last `tasks: mark phase <n>` commit, which restarted a feature adopted
  partway through at Phase 1.)
- **The project names no suite, or no static check**: verification runs what is named, says in the
  completion report what was not, and the diff is read as always.
- **`[P]` tasks** run inside their phase's worker, one after another: two workers would write the
  same worktree and index at once.
- **`CLAUDE_CODE_SUBAGENT_MODEL` is set**: the worker still runs on the smaller model and the reviewer
  on the main session's family, because both calls name their model.
- **The project defines its own `general-purpose` agent**: it is used for workers and reviews, with
  its own prompt; the calls' model and effort still apply (observed, R1).
- **The main session is already on the smaller model**: the hand-off still happens; not measured.
- **The project is not a git repository**: core runs without git, the hand-off cannot (per-task
  commits, the diff from a recorded HEAD): the run falls back to core (FR-007).
  Not measured, the eval's fixture being a git repository; the source is core itself, whose
  "Project Setup Verification" checks `git rev-parse --git-dir` before relying on git (constitution
  III's cited source, for a rule that restates core's behaviour).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The fragment MUST hand each phase of `tasks.md` to one worker, in the order core runs
  them, the next only after the previous one's verification, with no two workers active at once.
- **FR-002**: The worker MUST be started with `subagent_type: "general-purpose"`, `model: "sonnet"`
  (the family alias, so a newer model of the family is picked up without a release),
  `effort: "medium"` and `run_in_background: false` on the call, so the main session has the
  worker's report before it verifies (research.md R1 17).
- **FR-003**: The worker's brief MUST open with the phase's heading as `tasks.md` writes it and carry
  the phase's unmarked tasks, which may already be partly done (0.2.0, feature 003) — or, for a
  fix, the finding — the feature directory, the suite and static-check commands (from the
  project's instructions, else `plan.md`'s Technical Context), and the phases already marked; it
  MUST point the worker at core's "Load and analyze the implementation context", "Project Setup
  Verification" (Phase 1's worker only, 0.2.0), "Execute implementation", "Implementation execution rules" and
  "Progress tracking and error handling" steps in the composed skill rather than repeating them; and
  it MUST say the worker commits each task in a commit of its own (0.2.0: staging only the files it
  changed, never a file in the feature directory), returns the worker report, follows
  or reports a call a project hook blocks, and does not edit `tasks.md` (core's "mark the task off as
  [X]" in those steps is the main session's), start a review or start another worker.
- **FR-004**: The main session MUST mark a task `[X]` only after, in its own runs, the whole suite
  passes (when one is named), the static checks report no finding the baseline it took before the
  phase's first worker did not have (when they are named), and its reading of the phase's diff finds
  nothing the phase's tasks do not call for (0.2.0: the commits since the recorded HEAD, and `git
  status` listing nothing uncommitted outside the feature directory; a task found
  already done is marked on the suite, the static checks and the commit or file cited). A review the phase calls for (FR-005), and every fix
  it leads to, resolves before the phase is marked; then the main session commits `tasks.md` with a
  message containing `tasks: mark phase <n>` (after any prefix the project's instructions require), and only then does the next phase's worker start. A worker's report
  never marks a task.
- **FR-005**: Any review the user's or the project's instructions, or a command, call for MUST be
  started in a fresh context with `subagent_type: "general-purpose"`, `model` set to the main
  session's model family and no `effort`, so it inherits the main session's; never run by a worker.
  Where no fresh context can be started (no Agent tool, or the call errors), the review does not run
  and the completion report says so: core has no review, and a review by the context that wrote the
  code is not one.
- **FR-006**: Every hand-off — unfinished tasks, a failed verification, a review finding — MUST go
  to a worker briefed with it (0.2.0: except a task that changes the feature directory, which the
  main session carries out), then verification again; a review finding passes when a fresh review
  of that finding no longer reports it. A phase gets at most two fix hand-offs — every hand-off of
  the phase after its first counts, whatever items it carries; when verification — a fresh review still reporting its finding included — still fails after
  them, the main session carries out the phase's
  remaining items itself as core does (FR-007). Tasks a worker reported finding join the current
  phase in `tasks.md` (committed with a message containing `tasks: add found tasks`) and go to its next hand-off. A task a
  project hook blocked is not handed off again: it stays unmarked, goes into the completion report,
  and the next phase starts without it — unless the suite is red because of it, in which case core's
  "Halt execution if any non-parallel task fails" applies and the run ends with the report. Apart
  from that, the main session's only edits to tracked files are `tasks.md` — its checkboxes, and the
  tasks a worker reported finding — and its commits of them; running the suite, the static checks or
  core's extension hooks is not writing code. (0.2.0: outside the items it carries out, and it commits
  what it carries out outside the feature directory with a message containing `tasks: carried out
  in this session`.)
- **FR-007**: When no worker can carry on — no Agent tool, a worker's error (a usage limit included)
  or missing report, or a project that is not a git repository (the hand-off's commits, diff and
  baseline need git), or (0.2.0) uncommitted changes outside the feature directory when the run
  starts — the main session MUST carry out the remaining tasks as core does and say which
  and why in the completion report (constitution IV). FR-006's bound is narrower: only that phase's
  remaining items run in the main session, and the next phase goes to a worker as usual. The completion report always
  carries the line `Carried out in this session: none`, or `Carried out in this session:` followed by
  the task ids and, for fix items, the phase and a short name of each.
- **FR-008**: The fragment MUST name each core rule it narrows — "For completed tasks, make sure to
  mark the task off as [X]", "parallel tasks [P] can run together" and "Halt execution if any
  non-parallel task fails" — and the composition test MUST fail when core no longer carries one, or
  no longer has a step the brief names (constitution I).
- **FR-009**: The README MUST record the eval of User Story 2 with everything its Independent Test
  lists, and that one synthetic feature is less representative than a real one.
- **FR-010**: The fixture, its held-out tests, the probes and the harness MUST live under `tests/`,
  outside the release archive (constitution V), with the steps to rerun them.
- **FR-011**: An eval arm MUST count only when the agent exited 0 within its deadline, and its result
  reports no error — and, for `without` and `fallback`, no permission denial and, for `without`, at
  least one review call (an Agent call with `subagent_type: "general-purpose"`, the tool's default,
  that returned without an error) per user story; and the `init` event shows the hermetic isolation held (output style `default`,
  no MCP server, no plugin outside Claude Code's built-in ones); otherwise the harness
  records it as not counted, with the reason, and writes no usage or held-out result for it.
- **FR-012**: The probes MUST rerun each observation of research.md R1 the design rests on that can
  be rerun without writing to the user's own configuration, print the Claude Code version they ran
  on, and fail when one no longer holds; the isolation observations (R1 6, 12) are checked instead on
  every eval run, from its `init` event.
- **FR-013**: On release, dotfiles' `sdd-init` MUST install the preset beside `constitution-authoring`,
  with its check seen red; dotfiles' effort policy MUST name the exception and link the decision; and
  each existing Spec Kit project MUST get the preset only with the owner's approval, in a commit of its
  own.

### Key Entities

- **Worker**: a subagent started for one hand-off with `subagent_type: "general-purpose"`,
  `model: "sonnet"`, `effort: "medium"` and `run_in_background: false`.
- **Hand-off**: everything FR-003 lists, and what the worker must not do.
- **Worker report**: the commits it made (first and last), the tasks done and, for each not done,
  what stopped it, anything it found that no task covers, and the output of its last whole-suite
  run.
- **Eval arm**: `without` (no preset), `with`, `fallback` (`with`, no Agent tool); per arm, its
  status, usage per model and in total, held-out results, suite result, stream and versions.
- **Probe**: one observation of R1, rerun headless, with its expected outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the fixture, the `with` arm's total usage — every model's, the main session's
  verification and any review included — is at least 30% lower than the `without` arm's.
- **SC-002**: On the fixture, the `with` arm passes at least as many held-out acceptance tests as
  `without`, and its own suite is green at the end.
- **SC-003**: In the `with` arm, as `tests/eval/attribution.py` reports it: every Write, Edit or
  NotebookEdit call the main session makes targets the feature's `tasks.md` (its shell commands are
  listed beside the result, for a reviewer to confirm none writes code); `modelUsage` has a Sonnet
  entry; every worker call (`model: "sonnet"`) is in the foreground (`run_in_background: false`),
  each phase heading of the fixture's `tasks.md` is the first line of at least one of their briefs
  (heading and emphasis marks aside), and none
  starts while another has not returned its result (FR-001); among the commits after the setup commit, at least one changes more than `tasks.md`, and
  every such commit's message starts with `fixture:`; the completion report says `Carried out in this
  session: none`; and the result has no `permission_denials` (a worker reaching for a tool outside
  the list is the feature misbehaving, not the environment).
- **SC-004**: The composition test goes red when a core rule FR-008 names, or a core step the brief
  names, is removed, seen red once before it is trusted.
- **SC-005**: The `fallback` arm passes at least as many held-out tests as `without`, makes no Agent
  call, and its completion report says `Carried out in this session:` followed by every task id.
- **SC-006**: Every probe passes on the Claude Code version the eval ran on.
- **SC-007**: In the `with` arm, the stream holds at least one review call per user story: an Agent
  call with `subagent_type: "general-purpose"` and `model: "opus"`, the main session's family (calls
  of other subagent types, such as `Explore`, are not reviews). The same count in `without`, where a
  review is any `general-purpose` call, is a condition of the comparison, not of the preset: a
  `without` arm with fewer reviews than stories is rerun (FR-011).

## Assumptions

- Nothing is installed in a project for the worker (research.md R1).
- The eval pins the main session to Opus at `--effort medium`, its default today; another model or
  effort is not measured, and the README says so.
- Usage is compared by the per-model cost Claude Code reports for a headless run (list price,
  subagents included). The subscription window's utilization the stream also reports is recorded
  beside it, not used for SC-001: it moves with any other session on the account.
- Held-out acceptance tests — at least one per acceptance scenario of the fixture's spec, against the
  interface its plan fixes — judge every arm by the same oracle; the agent's own tests differ between
  arms and are not compared.
- The hermetic eval leaves in what no flag removes: admin-managed settings and Claude Code's built-in
  skills and plugins; the harness records which loaded.
- Agents other than Claude Code fall back to core (FR-007).
