---

description: "Task list for 002-large-phase-remeasure"
---

# Tasks: Large-phase remeasure

**Input**: Design documents from `specs/002-large-phase-remeasure/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/harness.md, quickstart.md

**Tests**: requested for every story with logic of its own (the owner's rules): the fixture's oracle
(US1); `usage.py` and `run.sh`'s changes (US2); `compare.py`, `runs.sh` and the SC-004 red check
(US3). Test tasks come first in each story; their red run is one per story's test tasks, each failure
checked against the reason its case predicts (a missing name proves only collection: stub it and
rerun). Each story closes with the whole suite (`tests/check.sh`) and a fresh-context review.

**Organization**: by user story. US1 and US2 are both P1 and independent of each other once the
foundational move is done; US3 needs both; US4 runs only on a pass.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1, US2, US3, US4

---

## Phase 1: Setup

**Purpose**: the feature's pull request, so CI runs on every push (the owner's rule: with CI on pull
requests, the PR opens as a draft).

- [X] T001 Commit the feature's design documents (`specs/002-large-phase-remeasure/`), push branch `002-large-phase-remeasure`, and open its PR as a draft with `gh pr create --draft`, so `compose (pinned)` runs on every push

**Checkpoint**: the draft PR exists and its CI is green on the documents-only commit.

---

## Phase 2: Foundational

**Purpose**: one layout for every fixture and the fixture argument (research R6), which US1's new
fixture and US2's harness changes both build on.

- [X] T002 Extend `tests/eval/test_run.py` first: the stub layout moves to `tests/eval/fixtures/<name>/{project,heldout}`; `run.sh <fixture> <arm> <out-dir>` refuses (exit 2, nothing written) an unknown fixture and one lacking `project/` or `heldout/`; a counted run's `versions.txt` carries `fixture: <name>` and `arm: <arm>`; the scratch repository is a copy of `fixtures/<name>/project/` and `tests_heldout/` of `fixtures/<name>/heldout/`; run `uv run pytest tests/eval/test_run.py` and see the new cases fail for the predicted reason (the old two-argument call)
- [X] T003 `git mv tests/eval/fixture tests/eval/fixtures/wordstats/project`, `git mv tests/eval/heldout tests/eval/fixtures/wordstats/heldout`, `git mv tests/eval/reference tests/eval/fixtures/wordstats/reference`, unchanged; set `pyproject.toml`'s pytest `norecursedirs` to `["fixtures"]` and rewrite the comment beside it (the fixtures' projects, held-out tests and reference implementations are run by the eval and the oracle proofs, against their own interpreter setup)
- [X] T004 Change `tests/eval/run.sh` to `run.sh <fixture> <arm> <out-dir>` (contract `run.sh`, first two bullets) and add `fixture` and `arm` to `versions.txt`; update the usage line and header comment; T002's cases pass unchanged, and `tests/check.sh` passes
- [X] T005 Update every reference to the old layout and call: `CLAUDE.md`'s Commands (`tests/eval/run.sh <fixture> <without|with|fallback> <out-dir>`), and the wordstats oracle proof through a new `tests/eval/oracle.sh <fixture>` (tests first in `tests/eval/test_oracle.py`; contract `oracle.sh`): `oracle.sh --write-n wordstats` passes and records `fixtures/wordstats/heldout/N`, and quickstart step 0 runs `oracle.sh` (spec US1 scenario 4). That the harness accepts wordstats is shown by T002's stub tests and the oracle, not by a real run, which would spend usage

**Checkpoint**: `tests/check.sh` green; `wordstats` still accepted by the harness and its oracle passes.

---

## Phase 3: User Story 1 - A fixture with room to differ (Priority: P1) 🎯 MVP

**Goal**: the `checkout` fixture: three story phases of 6–10 tasks each, difficulty only from what its
spec states, held-out tests traced to scenarios, proven by a reference implementation (research R5).

**Independent Test**: spec US1's: the task counts, the held-out traceability reviewed with no open
finding, the oracle passing, and (later, in US3's eval) a `without` run missing a held-out test.

### The fixture's feature (what the agent gets)

- [X] T006 [US1] Create `tests/eval/fixtures/checkout/project/` as a uv Python project like `fixtures/wordstats/project/` (`requires-python >=3.11`, run on 3.12) (`pyproject.toml` with dev pytest and ruff, a committed `uv.lock`, `.gitignore`), `CLAUDE.md` copied from `fixtures/wordstats/project/CLAUDE.md` with only the heading (`# checkout`), the one-line description and the review's spec path (`specs/001-checkout/spec.md`) changed (FR-001; `diff` the two files and see only those three lines differ), and `.specify/feature.json` pointing at `specs/001-checkout`; no `checklists/`, no `src/` code
- [X] T007 [US1] Write `tests/eval/fixtures/checkout/project/specs/001-checkout/spec.md`: a cart-pricing feature in three stories headed `### User Story <n> - <title> (Priority: P<n>)` as wordstats' are (the harness counts that heading), every rule stated as an acceptance scenario numbered `US<n>-<m>`, money as decimal cents, and every tie a rule can meet given a stated tie-break with its own scenario (equal exclusive and non-exclusive discounts: the exclusive applies; equal remainders in a largest-remainder allocation: the leftover cent goes to the earlier line, or for refunds the earlier unit). **US1 catalog, cart and tax**: a catalog of SKUs with unit price and category; a cart of lines (SKU, quantity 1–99, an unknown SKU or a quantity outside 1–99 rejected with a stated error); tax per category rate, computed per line on the line's net amount and rounded half-even to the cent; order total = lines' net + lines' tax; a zero-priced item and a 0% category stated. **US2 promotions**: percentage off a category, buy-X-get-Y-free on a SKU (the cheapest qualifying units free), a fixed amount off the order (never below zero), a per-order cap on total discount; stated stacking order (buy-X-get-Y, then percentage, then fixed, then cap); promotions flagged exclusive apply alone, the larger discount of best-exclusive versus all-non-exclusive wins; an order-level discount is allocated to lines in proportion to their net by largest remainder, so tax applies to discounted line amounts. **US3 returns**: returning units of a line refunds those units' share of the line's discounted net plus its tax, discounts fixed at purchase (never re-evaluated); per-unit amounts allocated by largest remainder so a fully returned order's refunds sum exactly to what was paid; several partial returns never exceed it; returning more units than remain is rejected. Each story 5–8 scenarios, edge cases among them (a cap reached mid-order, a free unit at zero price, a leftover cent)
- [X] T008 [US1] Write `.../specs/001-checkout/plan.md`: Technical Context naming `uv run pytest` and `uv run ruff check`; fix the interface the held-out tests use — modules `src/checkout/{money,catalog,cart,tax,promotions,allocation,returns}.py`, each public function and dataclass with its signature and errors (exception class names) — so held-out tests can be written against it
- [X] T009 [US1] Write `.../specs/001-checkout/tasks.md`: `## Phase 1: Setup`, then `## Phase 2: User Story 1 …`, `## Phase 3: User Story 2 …`, `## Phase 4: User Story 3 …` (numbered from 1 in order, FR-013), each story phase 6–10 task lines, test-writing tasks included and first, each task naming its files, each phase's tasks spanning three or more of the plan's modules (FR-002 (c)); count the lines per phase and record the counts in the task's commit message

### Tests for User Story 1 (the oracle; written before the reference)

- [X] T010 [US1] Write `tests/eval/fixtures/checkout/heldout/`: at least one test per acceptance scenario of T007's spec, against T008's interface only; each test's docstring names its scenario (`US<n>-<m>`) and quotes the spec sentence or sentences its expected values follow from (FR-002); no test of anything the spec does not state
- [X] T011 [US1] Red run: the held-out tests against the fixture as committed (no code) fail for the predicted reason (import of `checkout` modules fails); then against stubs of T008's interface raising `NotImplementedError`, each fails on its own call

### Implementation for User Story 1

- [X] T012 [US1] Write `tests/eval/fixtures/checkout/reference/src/checkout/` implementing T008's interface to T007's spec
- [X] T013 [US1] Prove the oracle: `tests/eval/oracle.sh --write-n checkout` passes, recording `tests/eval/fixtures/checkout/heldout/N` (data model, "Held-out score"); commit it, then `tests/eval/oracle.sh checkout` passes; then for each story, a wrong version in a scratch copy (tax rounded half-up; stacking order swapped; refunds without largest remainder) turns at least one of its held-out tests red
- [X] T014 [US1] Fresh-context review of the held-out tests (FR-002): a reviewer that did not write them checks each against its quoted spec text, the closed list of difficulty sources and the ambiguity test; write its findings and how each was resolved to `specs/002-large-phase-remeasure/heldout-review.md`; close every finding (a fresh review of the changed test finds it settled, or the recorded reason for leaving it unchanged sound); rerun T013 after any change

**Checkpoint**: `tests/check.sh` green; T009's counts in range; `heldout-review.md` has no open finding; a fresh review of US1 against spec US1 and FR-001–FR-002, its findings fixed.

---

## Phase 4: User Story 2 - The usage is attributed (Priority: P1)

**Goal**: every counted run's tokens and cost reconciled with what Claude Code reported and split by
part and phase (contract `usage.py`, `run.sh`; data model "Usage attribution").

**Independent Test**: spec US2's: on a counted run, reconciled per SC-008, parts summing to totals;
an unreconciled run not counted.

### Tests for User Story 2 (write first, see them fail)

- [X] T015 [P] [US2] Write `tests/eval/test_usage.py` against synthetic run directories (a `stream.jsonl` with `init` and `result` events, `transcripts/` with a main transcript and `subagents/agent-*.{jsonl,meta.json}`, `versions.txt`, a fixture `tasks.md`): reconciled → `usage.json`/`usage.txt` as the contract formats them, parts summing exactly in tokens and within $0.000001 in cost; per-entry duplicates merged by `message.id`, the last entry's usage counted once; prices from research R1 4 reproducing 001's four `costUSD` figures from their token counts ($0.5985348, $0.753208, $0.2320418, $0.4040008); each reconciliation reason on its own (`no transcript`, a token field off by one, cost off by more than $0.000001, `<model> price unknown`, an unparsable transcript line) → exit 1, nothing written; subagent parts (`sonnet` → worker; `general-purpose` with `opus`, `inherit` or no model → review; `Explore` → other); FR-013 spans: a well-formed four-phase session (setup included), preparation between phases going to the next phase, a phase never marked, a marking before its start, phase 2 handed off before phase 1's marking, a failed marking commit then a successful one (the successful one marks), two markings in one Bash call with the next start after it (the first of the two phases holds, the second breaks: FR-013), phase 1 breaking (whole session unattributed), no `after` after a break; a worker's phase from its brief's heading, a review's from its span, `null` outside; `without`/`fallback` main as one part; `--price-only`; exit 2 only for an internal fault
- [X] T016 [P] [US2] Extend `tests/eval/test_run.py`: `DISABLE_AUTOUPDATER=1` reaches every step's environment (the stub `claude` records its env); `versions.txt`'s pre-run keys exist before the stub agent starts (the stub reads them) and post-run keys after; `--baseline` with a differing pre-run key other than `arm` refuses (exit 2, the stub agent never invoked, `status` naming the key), with only `arm` differing proceeds; a differing `init`-event key → not counted; transcripts copied from a stub `$HOME/.claude/projects/<slug>/` whenever the stream names a session, a killed run included; a stub `usage.py` exit 1 → `not counted: unreconciled: …`, no `usage.*`/`suite.txt`/`heldout.txt`, exit 1; exit 2 → `refused: harness fault: …`, exit 2; the old jq `usage.txt` gone (usage.txt is `usage.py`'s)
- [X] T017 [P] [US2] Add to `tests/eval/test_run.py` (or a probes test beside it) a check that `tests/eval/probes.sh` passes `DISABLE_AUTOUPDATER=1` to its clean environment, against a stub `claude`
- [X] T018 [US2] Red run of T015–T017 against a stub `tests/eval/usage.py` raising `NotImplementedError` and the unchanged `run.sh`/`probes.sh`: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` clean first, then `uv run pytest`, each failure checked against its case's predicted reason

### Implementation for User Story 2

- [X] T019 [US2] Write `tests/eval/usage.py` (contract `usage.py`; data model "Usage attribution"; spec FR-013): stdlib only, typed for mypy strict; the price table with its source URL `https://platform.claude.com/docs/en/about-claude/pricing` and the date read `2026-10-14`
- [X] T020 [US2] Change `tests/eval/run.sh` (contract `run.sh`): `DISABLE_AUTOUPDATER=1` in the clean environment; `versions.txt` split into pre-run keys written before the agent and post-run keys after (data model); `--baseline`; transcript copy whenever a session is named; `usage.py` in counting before the suite with its exit mapping; 001's jq `usage.txt` block removed
- [X] T021 [US2] Add `DISABLE_AUTOUPDATER=1` to `tests/eval/probes.sh`'s clean environment
- [X] T022 [US2] Green run: T015–T017 pass unchanged; `tests/check.sh` passes
- [X] T023 [US2] Replay check on 001's real runs: build run directories from the three 001 streams and their transcripts still on this machine (research R1), run `usage.py` on each, and see it reconcile and reproduce research R2's table (main $0.382 / $0.505, reviews, workers); record the output in the commit message. Where those files are gone, say so in the commit message instead

**Checkpoint**: `tests/check.sh` green; a fresh review of US2 against spec US2, FR-004, FR-005, FR-013, SC-008 and the contract, its findings fixed.

---

## Phase 5: User Story 3 - The decision carries its measurement (Priority: P2)

**Goal**: the verdict computed (`compare.py`), each confirmed step driven (`runs.sh`), SC-004
observed, the eval run, and the outcome recorded.

**Independent Test**: spec US3's: the README entry with every FR-009 field, the outputs committed
under `tests/eval/results/002-large-phase-remeasure/`, the outcome agreeing with `preset.yml`, the
CHANGELOG and the tags.

### Tests for User Story 3 (write first, see them fail)

- [X] T024 [P] [US3] Write `tests/eval/test_compare.py` against synthetic committed run directories (data model "Comparison", "Spend"): medians and min/max for three runs; SC-001 at exactly 30% (passes), just under (fails); SC-002 on a held-out median tie (passes) and one red `with` suite (fails); held-out score as passed of the fixture's fixed N, an errored test not passed; SC-003 one clause `FAIL` in one run fails it; SC-005's report clause using the fixture's `tasks.md` ids; SC-006 version compared as `major.minor.patch` (`claude 2.1.299 (Claude Code)` against `claude: 2.1.299`), a probe `FAIL` fails it; SC-007 against the fixture spec's story count; SC-008 from `usage.json`'s `reported`/`transcripts`; refusals (a non-`ok` status, an arm with two or four runs, mixed fixtures, a versions key differing other than `date`/`arm`); `--gate` open and closed; `--spent` over runs and probe streams (`r*.jsonl`), a killed try priced from transcripts, a refused try as zero, an empty root as `spent 0`, `--next` estimates (an arm with counted runs, one without, none at all scaled from 001's `without` by task count, two arms summed, worst case ×3); held-out N read from `fixtures/<fixture>/heldout/N`
- [X] T025 [P] [US3] Write `tests/eval/test_runs.py` against a stub `run.sh` and stub `claude --version`: three counted runs per arm, arms alternating per round; a run tried at most three times (two reruns), then exit 1; `--baseline` passed once `without-1` exists, not before; refusals leaving a `status` (`probes.txt` missing, a probe `FAIL`, a version differing from `claude --version`, the gate closed for `with`/`fallback`, `run.sh` exit 2) with exit 2 and no further try; links relative
- [X] T026 [P] [US3] Add to `tests/compose.sh` the SC-004 red check (spec SC-004): for each anchor of `tests/core-anchors.sh`, a copy of the core `speckit-implement` skill with that anchor's text removed makes `tests/core-anchors.sh` exit 1 naming it; written first against a deliberately broken copy of `tests/core-anchors.sh` (one anchor dropped) to see the new check go red for that anchor
- [X] T027 [US3] Red run of T024–T025 against stub `compare.py` and `runs.sh` (raising / exiting 99), lint and type checks clean first, each failure checked against its predicted reason

### Implementation for User Story 3

- [X] T028 [US3] Write `tests/eval/compare.py` (contract `compare.py`; data model "Comparison", "Spend", "Held-out score"): stdlib only, typed for mypy strict, reading the fixture's spec, `tasks.md` and `heldout/N` from `tests/eval/fixtures/<fixture>/` through the `fixture` key, and the unmeasured estimate's sources (001's `tests/eval/results/2026-10-14/without/usage.txt` `sum`, the two fixtures' task-line counts) as the data model names them
- [X] T029 [US3] Write `tests/eval/runs.sh` (contract `runs.sh`; research R11)
- [X] T030 [US3] Green run: T024–T026 pass unchanged; `tests/check.sh` passes (compose.sh's SC-004 check included); update `quickstart.md`'s SC-004 paragraph to name `tests/compose.sh` as the check and its output as `sc004.txt`; add `runs.sh`, `compare.py` and `usage.py` to `CLAUDE.md`'s Commands, pointing at this feature's `quickstart.md`

### The measurement (spends usage; every set confirmed by the owner)

- [ ] T031 [US3] Quickstart step 0 for attempt 1: `tests/check.sh`; `git diff 894aecf -- commands/ preset.yml` shows no change to the fragment or its template entry (FR-006; recorded for the README); probes into `$A/probes.txt`; the oracle (T013) and `heldout-review.md` closed. A red probe stops the eval → T034, then T035 (not measured)
- [ ] T032 [US3] Quickstart step 1: show `compare.py --spent /tmp/remeasure --next without`; **owner confirms**; `runs.sh "$A" checkout without`; `compare.py --gate`. Gate closed → harden per research R5 (spec FR-001's ten-task bound; T010–T014 repeated for what is added), commit, new attempt from T031, at most twice; a third closed gate, or `runs.sh` exit 1, → T034, then T035 (not measured); `runs.sh` exit 2 → read the try's `status`, fix and commit a harness fault (nothing to fix for a version change), new attempt from T031
- [ ] T033 [US3] Quickstart step 2: show `compare.py --spent /tmp/remeasure --next with fallback`; **owner confirms both sets**; `runs.sh "$A" checkout with fallback`; `attribution.py` into each `with` run's `attribution.txt`; `compare.py --probes` into `compare.txt`; `tests/compose.sh` on the measured commit into `sc004.txt`; `runs.sh` exit 1 → T034, then T035 (not measured); exit 2 as in T032
- [ ] T034 [US3] Whatever the outcome, copy every attempt into `tests/eval/results/002-large-phase-remeasure/attempt-<k>/` as spec FR-012 lists (no streams, no transcripts; relative links kept)
- [ ] T035 [US3] Write the README entry `Eval 002, <date>` with every field of spec FR-009, from `compare.txt`, the runs' `usage.txt` and the statuses; then the outcome: pass → spec US3 scenario 1 (README status line; `preset.yml` keeps `0.1.0`, its comment names the release; `CHANGELOG.md` created, Keep a Changelog, entry `0.1.0`); fail → US3 scenario 2 (each failed criterion, value against threshold, the attribution's reading; README status line, `preset.yml` comment and `CLAUDE.md` description naming both measurements); stopped → US3 scenario 6. In every branch, update `docs/decisions/0001-worker-effort.md`'s status line so it stays true (adopted with `v0.1.0`; or not adopted, citing both measurements)

- [ ] T036 [US3] Pass only: in `README.md`, the install section (from the `v0.1.0` archive), what the preset narrows, its limits and "when not to use it" (a main session already on the smaller model; agents without subagents)

**Checkpoint**: `tests/check.sh` green; a fresh review of US3 (harness, the README entry against the committed outputs). **Decision**: pass → Phase 6 (T037–T039, then the release, T040), then Phase 7, which needs the tag; fail or stopped → Phase 6 (T037–T039, then T041), and Phase 7 does not run.

---

## Phase 6: Polish, review and merge

- [ ] T037 Move research.md R3 (usage attribution from transcripts, reconciled on every run) to `docs/decisions/0002-usage-attribution.md` (MADR: context, options, outcome, consequences, linking R3): later evals build on it; `CLAUDE.md`'s pointer to `docs/decisions/` already covers it
- [ ] T038 Final sweep of `CLAUDE.md`: every statement true after this feature (its description line and Commands; earlier tasks edited parts of it), per the constitution's "correct it in the same commit that made it false"
- [ ] T039 `/speckit-converge` until a pass finds nothing above LOW; its tasks, if any, implemented before T040/T041
- [ ] T040 Pass only: a fresh-context review of the whole diff, its findings fixed; then **the owner reviews the PR against constitution principles I–V** (constitution, Governance) and, on their approval, mark it ready (`gh pr ready`) and merge with `gh pr merge --auto --squash` on green `compose (pinned)`; tag `v0.1.0` on the merge commit and push the tag
- [ ] T041 Fail or stopped only: a fresh-context review of the whole diff, its findings fixed; tag the measured state `measured-not-adopted-002-<date>` (fail only); then **the owner reviews the PR against constitution principles I–V** and, on their approval, mark it ready and merge with `gh pr merge --auto --squash` on green `compose (pinned)`; no version tag

---

## Phase 7: User Story 4 - The owner's setup adopts a released preset (Priority: P3)

**Goal**: spec FR-010, only after the release (T040).

**Independent Test**: spec US4's.

### Tests for User Story 4 (write first, see them fail)

- [ ] T042 [US4] In dotfiles, on a branch of its own: extend `~/dotfiles/checks/90-spec-kit.sh` to require `PRESET_STORY_WORKERS_URL` pointing at this repository's `v0.1.0` archive and `sdd-init` installing it after `constitution-authoring`; run `./check.sh` and see it fail for the missing URL

### Implementation for User Story 4

- [ ] T043 [US4] Add `PRESET_STORY_WORKERS_URL` and its `specify preset add` to `~/dotfiles/bin/sdd-init.sh` (header comment and commit message updated); `./check.sh` green; `sdd-init` in a scratch repository installs both presets
- [ ] T044 [US4] In `~/dotfiles/docs/claude-settings.md`, name the worker's `effort: "medium"` as the one exception to the effort policy, its reason in one line, linking this repository's `docs/decisions/0001-worker-effort.md`
- [ ] T045 [US4] Open the dotfiles PR (draft → fresh review → ready → `gh pr merge --auto --squash` on green CI)
- [ ] T046 [US4] For each existing Spec Kit project the owner names: ask; on a yes, `specify preset add --from <v0.1.0 archive>`, confirm with `git status` that only the preset's files changed, and commit exactly those in a commit of their own through that repository's PR rules

---

## Dependencies & Execution Order

- Setup (T001) → Foundational (T002–T005) → US1 (T006–T014) and US2 (T015–T023), independent of
  each other → US3 (T024–T036; its measurement needs US1's fixture and US2's attribution) → Polish,
  review and merge (T037–T039, then T040 on a pass or T041 otherwise) → US4 (T042–T046) only after
  T040's tag.
- Nothing lands after the PR is marked ready: every change to the README, the decision records,
  `CLAUDE.md` and converge's tasks comes before T040/T041, so the tagged archive carries them.
- Within each story, tests (and their red run) precede the code they drive.
- T032 and T033 each wait for the owner's confirmation; T040 and T041 wait for the owner's review.

## Parallel Opportunities

- US1 and US2 after Phase 2; within US2, T015–T017; within US3, T024–T026.
- `[P]` marks independence. Under this preset's own fragment, `[P]` tasks run one after another inside
  one worker.

## Implementation Strategy

- MVP: US1 and US2 (the fixture with its proven oracle, and attributed usage), which make the eval
  worth running; US3 runs it and decides; US4 only on a pass.
- A negative result (not adopted) or a stop (not measured) is a valid outcome, recorded as such.
