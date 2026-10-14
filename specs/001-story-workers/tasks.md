---

description: "Task list for 001-story-workers"
---

# Tasks: Story workers

**Input**: Design documents from `specs/001-story-workers/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/fragment.md, quickstart.md

**Tests**: requested for every story with logic of its own (the owner's rules): the composition
checks (US1), `bounded.py`, `attribution.py`, `run.sh`'s refusals and counting, and the held-out
tests (US2), the `sdd-init` check (US3). Test tasks come first in each story; their red run is one
per story's test tasks, and each failure is checked against the reason its case predicts (a missing
name proves only collection: stub it and rerun). Each story closes with the whole suite
(`tests/check.sh`) and a fresh review.

**Organization**: by user story; US2's release decision gates US3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup

**Purpose**: the repository's own toolchain and CI (plan, Phase 1).

- [ ] T001 Add the dev tooling with `uv add --dev ruff mypy pytest pytest-timeout` in `pyproject.toml` (package = false, ruff target py311 line length 100, mypy strict over `tests/eval`, pytest testpaths `tests/eval`, timeout 60) and commit `uv.lock`
- [ ] T002 [P] Add `pyproject.toml` and `uv.lock` to `.gitattributes` as `export-ignore`
- [ ] T003 Write `tests/check.sh`, the one command: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run pytest`, then `tests/compose.sh` (exits non-zero on the first failure, says which)
- [ ] T004 Write `.github/workflows/ci.yml`: job `compose`, matrix `speckit: [pinned, latest]` with latest only on schedule and dispatch, `SPECKIT_PINNED: v1.1.0`, actions pinned by SHA as in `spec-kit-preset-constitution-authoring/.github/workflows/ci.yml`, installs `specify` and uv, runs `tests/check.sh`
- [ ] T005 Add `CLAUDE.md`'s Commands section with `tests/check.sh` and the eval and probe invocations from `specs/001-story-workers/quickstart.md`, in `CLAUDE.md`

**Checkpoint**: `tests/check.sh` runs (it fails only on the missing `tests/compose.sh`, which US1 writes).

---

## Phase 2: Foundational

**Purpose**: the ruleset that makes `compose (pinned)` required (constitution, Governance).

- [ ] T006 In dotfiles, on a branch of its own: add `"camilopiedra92/spec-kit-preset-story-workers": {"checks": ["compose (pinned)"]}` to `~/dotfiles/github/repos.json`, run `./check.sh`, open its PR, and once merged run `bin/repo-rules.sh` so the ruleset applies (the check name exists once this feature's draft PR has run CI)

**Checkpoint**: the ruleset is declared; the feature's PR will wait for `compose (pinned)`.

---

## Phase 3: User Story 1 - A phase's tasks run in a worker (Priority: P1) 🎯 MVP

**Goal**: the fragment, composed onto core `speckit-implement` by the real CLI, says every rule of
`contracts/fragment.md`.

**Independent Test**: `tests/compose.sh` passes on the pinned Spec Kit and fails when any narrowed
rule or step is missing from core (SC-004); the end-to-end behaviour is US2's `with` arm.

### Tests for User Story 1 (write first, see them fail)

- [ ] T007 [US1] Write `tests/compose.sh` following `spec-kit-preset-constitution-authoring/tests/compose.sh`: archive HEAD with `git archive`, serve it from localhost, `specify init --here --force --integration claude --ignore-agent-tools` in a scratch repo, copy core's `speckit-implement` aside, `specify preset add`, then check: the composed skill keeps core's body and description and ends with the fragment; the archive carries none of `.specify/`, `.claude/`, `specs/`, `tests/`, `docs/`, `.github/`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`
- [ ] T008 [US1] Add to `tests/compose.sh` the core anchors, fixed-string (`grep -F`): `For completed tasks, make sure to mark the task off as [X]`, `parallel tasks [P] can run together`, `Halt execution if any non-parallel task fails`, `Load and analyze the implementation context`, `Project Setup Verification`, `Execute implementation`, `Implementation execution rules`, `Progress tracking and error handling`
- [ ] T009 [US1] Add to `tests/compose.sh` the composed-skill phrases of `contracts/fragment.md` §1–§11, each joined into one line first and matched with `grep -F`: the call's `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"`; "hand each phase to a worker"; "commits each task"; "marks a task [X] only after"; "at most two fix hand-offs"; `tasks: mark phase`; `tasks: add found tasks`; "with `model` set to this session's model family"; "carry out the remaining tasks in this session"; `Carried out in this session:`; each narrowed rule named
- [ ] T010 [US1] Red run: `tests/compose.sh` before the preset exists, expecting the install to fail for want of `preset.yml`; then a placeholder `preset.yml` and an empty `commands/speckit.implement.md` (stubs), rerun, and check each composed-phrase check fails for its own phrase; then, for each anchor of T008, a core copy with that phrase deleted turns its anchor check red — record the red outputs for the PR description

### Implementation for User Story 1

- [ ] T011 [US1] Write `preset.yml`: id `story-workers`, version `0.1.0` (1.0.0 only at release), `requires.speckit_version: ">=1.1.0"`, one `command` template `speckit.implement` from `commands/speckit.implement.md`, `strategy: "append"`, a description of what the fragment changes
- [ ] T012 [US1] Write the fragment `commands/speckit.implement.md` (no frontmatter): a `## Story workers` section stating `contracts/fragment.md` §1–§11 in imperative prose for the main session, naming each narrowed core rule by its exact text, with the fallback beside the hand-off (constitution IV)
- [ ] T013 [US1] Green run: `tests/compose.sh` and `tests/check.sh` pass; the tests are unchanged since T010

**Checkpoint**: the whole suite green; a fresh review of US1 against spec FR-001–FR-008 and `contracts/fragment.md`, its findings fixed, before Phase 4.

---

## Phase 4: User Story 2 - The release carries its measurement (Priority: P2)

**Goal**: the probes and the three-arm hermetic eval run, and their result decides the release.

**Independent Test**: `tests/eval/probes.sh` and `tests/eval/run.sh` produce the outputs
`quickstart.md` reads; the README entry carries everything US2's Independent Test lists.

### Tests for User Story 2 (write first, see them fail)

- [ ] T014 [P] [US2] Write `tests/eval/test_bounded.py`: a command that exits in time returns its status; one past the deadline is killed with its whole process group (a child that ignores SIGTERM included) and `bounded.py` exits 124; a missing command exits 127
- [ ] T015 [P] [US2] Write `tests/eval/test_attribution.py` against stub `stream.jsonl`/`commits.txt`/`status` files: each SC-003 clause passes and fails on its own (a main-session Write outside `tasks.md`; no Sonnet entry; no code commit; a code commit without `fixture:`; the setup commit ignored; the `Carried out in this session` line missing or not `none`; a permission denial), exit 2 on an unreadable input or a non-`ok` status, and the main session's Bash commands listed
- [ ] T016 [P] [US2] Write `tests/eval/test_run.py` with a stub `claude` (and stub `specify`) on `PATH` that emit canned streams: refusals exit 2 and write nothing (unknown arm, existing out-dir, uncommitted checkout, each missing tool); a run counts only as research.md R6 "Counting" says — exit non-zero, past the deadline, zero or two `result` events, `is_error: true`, a denial in `without`/`fallback`, fewer reviews than stories in `without`, a non-default output style or a non-built-in plugin or an MCP server in `init` — each writing `status` with its reason, no `usage.txt`/`heldout.txt`, exit 1; a counted run writes every output file of `contracts/fragment.md`
- [ ] T017 [US2] Red run of T014–T016 with stub modules (`bounded.py`, `attribution.py` raising `NotImplementedError`, `run.sh` exiting 99), each failure checked against its case's predicted reason

### Implementation for User Story 2

- [ ] T018 [P] [US2] Write `tests/eval/bounded.py`: runs a command in its own process group under a deadline, kills the group (SIGTERM, then SIGKILL after a grace period), exits 124 on the deadline
- [ ] T019 [P] [US2] Write `tests/eval/attribution.py` (contract `attribution.py`)
- [ ] T020 [US2] Write `tests/eval/run.sh` (contract `run.sh`): refusals, the clean environment for every step, git isolation, `bounded.py` deadlines (3600 s for the agent, 600 s otherwise), the arm's preset, the counting rules, the outputs, the kept `repo/`
- [ ] T021 [US2] Green run: T014–T016 pass unchanged; `tests/check.sh` passes

### The fixture and its oracle

- [ ] T022 [US2] Write `tests/eval/fixture/`: a uv Python project with a committed `uv.lock` (pytest, ruff), `CLAUDE.md` with the two rules of research.md R6, `.specify/feature.json`, and `specs/001-<slug>/spec.md`, `plan.md` (Technical Context naming `uv run pytest` and `uv run ruff check`, fixing the module and function names) and `tasks.md` for a two-story feature with a setup phase; no `checklists/`; no code yet
- [ ] T023 [US2] Write `tests/eval/heldout/`: at least one acceptance test per acceptance scenario of the fixture's spec, against the interface its plan fixes; and `tests/eval/reference/`, a correct implementation kept outside the fixture
- [ ] T024 [US2] Prove the oracle: the held-out tests fail on the fixture as committed (no code, each for the predicted reason), and pass against `tests/eval/reference/`; then one wrong version per story in a scratch copy turns them red

### The probes

- [ ] T025 [US2] Write `tests/eval/probes.sh` (contract `probes.sh`): R1 (1, 3, 4 with `sonnet` and `opus`, 5, 7, 8, 9, 10, 11, 15), hermetic, printing the Claude Code version and `ok`/`FAIL` per probe; exit 1 on any failure
- [ ] T026 [US2] Break each probe's expectation on purpose once (invert the expected outcome in a scratch copy) and see it go red; then `tests/eval/probes.sh` passes on the installed Claude Code (SC-006)

### The measurement and the decision

- [ ] T027 [US2] Run the three arms as `quickstart.md` says, back to back, with every try kept; confirm `versions.txt` matches across arms
- [ ] T028 [US2] Judge SC-001, SC-002, SC-003 (`attribution.py`), SC-005, SC-006 and SC-007 from the outputs, and write the README entry: the date, the fixture's size, every arm's outputs, reruns and reasons, `versions.txt`, `models.txt`, the probes' output, the isolation, "one counted run per arm, directional", and the limits (FR-009)
- [ ] T029 [US2] Move research.md R7 to `docs/decisions/0001-worker-effort.md` (MADR: context, options, outcome, consequences, linking R7), and point `CLAUDE.md` at `docs/decisions/`

**Checkpoint**: the whole suite green; a fresh review of US2 (harness, fixture, oracle, the README entry against the raw outputs) before the decision is acted on. **Decision**: every success criterion holds → Phase 5. Any does not → the README entry alone goes to `main` in its own PR, recording the rule as measured and not adopted; tag the branch `measured-not-adopted-<date>`, leave it unmerged, and stop here.

---

## Phase 5: Release (only on a pass)

- [ ] T030 Write `README.md`: what the preset does and what it narrows, install from the tag's archive, update, limits, the evidence (the eval entry, research R1's observations with their versions, Anthropic's multi-agent write-up), and "When not to use it" (a main session already on the smaller model; agents without subagents)
- [ ] T031 Write `CHANGELOG.md` (Keep a Changelog), entry `1.0.0`; set `preset.yml` version `1.0.0`
- [ ] T032 Open the feature's PR as a draft, mark it ready once a fresh review of the whole diff is back, merge with `gh pr merge --auto --squash` on green `compose (pinned)`, then tag `v1.0.0` on the merge commit and push the tag

---

## Phase 6: User Story 3 - The owner's setup adopts the released preset (Priority: P3)

**Goal**: new repositories get the preset; existing ones get it with the owner's approval; the
owner's policies stay true.

**Independent Test**: `sdd-init` in a scratch repository installs both presets; dotfiles'
`./check.sh` goes red when the story-workers URL is removed from `bin/sdd-init.sh`.

### Tests for User Story 3 (write first, see them fail)

- [ ] T033 [US3] In dotfiles, on a branch of its own: extend `~/dotfiles/checks/90-spec-kit.sh` to require `PRESET_STORY_WORKERS_URL` pointing at `spec-kit-preset-story-workers`'s tag archive and `sdd-init` installing it after `constitution-authoring`; run `./check.sh` and see it fail for the missing URL

### Implementation for User Story 3

- [ ] T034 [US3] Add `PRESET_STORY_WORKERS_URL` (the `v1.0.0` archive) and its `specify preset add` to `~/dotfiles/bin/sdd-init.sh`, update the header comment and the commit message it writes; `./check.sh` green
- [ ] T035 [US3] In `~/dotfiles/docs/claude-settings.md`, under "`effortLevel` is absent on purpose", name the one exception — the story-workers preset sets `effort: "medium"` on its worker's call — with its reason in one line and a link to the preset's `docs/decisions/0001-worker-effort.md`
- [ ] T036 [US3] Open the dotfiles PR (draft → fresh review → ready → `gh pr merge --auto --squash` on green CI)
- [ ] T037 [US3] For each of `~/Development/renta`, `~/Development/RENPHO`, `~/Development/supertrader` and `~/dotfiles`: ask the owner; on a yes, `specify preset add --from <v1.0.0 archive>` and commit only `.specify/presets/` and `.claude/skills/speckit-implement/` in a commit of its own, through that repository's own PR rules

**Checkpoint**: the whole suite green in dotfiles; a fresh review of the dotfiles diff.

---

## Dependencies & Execution Order

- Setup (T001–T005) → Foundational (T006) → US1 (T007–T013) → US2 (T014–T029) → decision → Release (T030–T032) → US3 (T033–T037).
- US2 needs US1: the `with` arm installs the fragment. US3 needs the released tag.
- Within US1 and US2, tests (and their red run) precede the code they drive.

## Parallel Opportunities

- T002 beside T001's lockfile commit; T014, T015, T016 together; T018 and T019 together.
- Under this preset's own rule, `[P]` tasks still run one after another inside one worker; here they mark independence, not concurrency.

## Implementation Strategy

- MVP: US1 (the fragment and its composition test) delivers a preset that installs and says the rules; it is not released until US2's measurement passes (constitution III).
- The measurement can end the feature at the US2 checkpoint: a negative result is a valid outcome, recorded as not adopted.
