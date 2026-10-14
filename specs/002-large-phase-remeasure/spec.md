# Feature Specification: Large-phase remeasure

**Feature Branch**: `002-large-phase-remeasure`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Remeasure the story-workers preset with a fixture whose phases are
large (6–10 tasks each) and hard enough that core `/speckit-implement` makes mistakes, reusing the
001 harness; record input and output tokens per model so the main session's per-phase verification
cost is measured instead of inferred; adopt and release, or record again as measured and not
adopted." (agreed with the owner on 2026-10-14, after feature 001's eval)

## Context

Feature 001 measured the story-workers fragment on 2026-10-14 (README, "Eval, 2026-10-14") and did
not adopt it: SC-001 failed, the `with` arm using 65% more than `without` ($0.985 against $0.599),
while every other criterion held and all three arms passed 12 of 12 held-out tests. Its fixture had
five tasks in three phases, one or two tasks each.

Two things that result could not settle:

- **Why `with` cost more.** The README's reading was an inference: each phase adds a fixed cost to
  the main session (a brief, a report, a suite and static-check rerun, a diff read), and phases of
  one or two tasks do not carry enough implementation work for moving it to the smaller model to pay
  for that. 001's harness recorded only cost and cache tokens per model. Attributed after the fact
  from the runs' session transcripts (research.md R2), the `with` main session, which wrote no code,
  cost $0.505 against $0.382 for the `without` main session, which wrote all of it: delegation did
  not shrink the main session on that fixture. How each arm grows with phase size is still unknown.
- **Quality.** Every arm passed every held-out test, so the fixture had no headroom to show the
  preset doing better or worse.

This feature remeasures the same fragment, unchanged, on a fixture built to settle both, with the
harness reporting where every token goes.

## Clarifications

### Session 2026-10-14

- Q: Does the fragment change? → A: no: this measures 001's fragment as merged, so a result is
  about phase size, not a new rule. A changed fragment is another feature with its own eval.
- Q: How is "hard enough that core makes mistakes" established? → A: the `without` arm's counted
  runs go first; when none of them misses a held-out test, the fixture has no headroom, so no
  `with` or `fallback` run is spent on it: the fixture is hardened and `without` runs again. No
  separate pilot: the gate reuses runs the eval needs anyway.
- Q: How many counted runs per arm, and how are disagreeing runs combined? → A: three per arm;
  SC-001 and SC-002 are judged on each arm's median, and the README gives every run with its spread
  (min and max) beside it. One run per arm, as in 001, lets one noisy run decide a release; the
  median of three tolerates one outlier run, where five or more runs per arm would also give a usable
  spread estimate at five thirds of the cost or more; a median of three says nothing about variance
  beyond the observed min and max, and the README says so.
- Q: What reduction must `with` show? → A: 30%, 001's bar: the remeasure answers 001's question,
  and a bar lowered after a failure would make the second eval easier than the first.
- Q: Where does the fixture's difficulty come from? → A: from what its spec states, never from a
  requirement the spec leaves out or words ambiguously; each held-out test traces to one acceptance
  scenario. A test of something the spec does not say measures luck, not the preset (decided on the
  owner's instruction to take the recommended option).
- Q: How many times may the fixture be hardened when `without` misses nothing? → A: twice; a third
  `without` set that misses nothing stops the eval, since the fixture's design, not its tuning, is
  then wrong (same instruction).
- Q: When does the owner confirm spending? → A: once before each arm's set of counted runs, with
  the usage spent so far and the estimate for the set; reruns of a run that did not count fall under
  that confirmation (same instruction).
- Q: After the second closed gate (six `without` runs, every held-out test passed), how does 002
  end? → A: the owner chose to stop measuring and release the preset as measured: the constitution
  was amended (v2.0.0, principle III) so a rule whose eval does not show its claimed effect can be
  released on the owner's recorded acceptance; the README records both evals as they came out and
  the decision beside them (US3 scenario 7). Decided by the owner, 2026-10-14, choosing between a
  third hardening, a cost-only run of `with` and `fallback`, and stopping.
- Q: Is a run whose usage cannot be reconciled a measurement? → A: no: the attribution is what this
  feature adds, so a run whose transcripts are missing or do not reconcile is not counted and is
  rerun within the usual bound; a part the harness cannot place in a phase is not a reconciliation
  failure but a finding, reported as `unattributed` (same instruction).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A fixture with room to differ (Priority: P1)

The owner needs a committed fixture feature on which delegation has enough work per phase to pay
off if it ever does, and on which core's own run is not perfect, so the eval can show a difference
in usage and in quality in either direction.

**Why this priority**: without it, a rerun repeats 001's result for 001's reason; every other story
depends on it.

**Independent Test**: the fixture's `tasks.md` has a setup phase and exactly three user-story
phases, each holding 6 to 10 tasks; its held-out tests cover every acceptance scenario of its spec,
each citing its scenario and the spec text its expected values come from; a fresh-context review of
that traceability has no open finding; the reference implementation passes every held-out test; and
at least one of the `without` arm's counted runs misses at least one held-out test.

**Acceptance Scenarios**:

1. **Given** the new fixture, **When** its `tasks.md` is read, **Then** every user-story phase holds
   6 to 10 task lines — test-writing tasks included — and each task names the files it changes.
2. **Given** the fixture's spec, **When** its held-out tests are listed, **Then** each acceptance
   scenario has at least one, written against the interface its plan fixes, each test's docstring
   names its scenario (`US<n>-<m>`) and quotes the spec sentence or sentences its expected values
   follow from, and none of them is in the fixture the agent sees.
3. **Given** a reference implementation written to the fixture's plan, **When** the held-out tests
   run against it, **Then** they all pass, so a failure in an arm is the arm's and not the oracle's.
4. **Given** 001's fixture on `main`, **When** this feature lands, **Then** the harness still accepts
   it and its reference implementation still passes its held-out tests; reproducing 001's measured
   numbers is done from its tag `measured-not-adopted-2026-10-14`, not from `main`.

---

### User Story 2 - The usage is attributed (Priority: P1)

The owner reading a result sees not only each model's total but where every token went: per model,
input, output, cache-read and cache-write tokens and cost; per subagent, whether it was a worker, a
review or something else; and, for `with`, the main session split into the work before the first
phase, each phase (preparing its hand-off, verifying, reviewing, marking), and the closing report.

**Why this priority**: the remeasure exists to test how the main session's cost grows with phase
size; without attribution, a second failure would again be explained by a guess.

**Independent Test**: on any counted run, the usage output reconciles with what Claude Code reports
for the run, and its parts — main session or its phases, workers, reviews, other subagents — sum to
the per-model totals, both as SC-008 defines (tokens exactly, cost within $0.000001).

**Acceptance Scenarios**:

1. **Given** a counted run, **When** its usage is written, **Then** it carries input, output,
   cache-read, 5-minute and 1-hour cache-write tokens and cost for every model in the run, and the
   sum, reconciled with what Claude Code reported as SC-008 defines.
2. **Given** a counted `with` run, **When** its usage is written, **Then** the main session is split
   by FR-013's spans into `before`, one part per phase of the fixture's `tasks.md` (its setup phase
   included), and `after`; every main-session turn falls in exactly one part.
3. **Given** a `with` run whose phase starts and markings are not in order (a phase never handed off
   or never marked, a marking before its hand-off, phases out of order), **When** the split is
   computed, **Then** the turns FR-013 names are `unattributed`, never folded into a phase, and the
   run still counts.
4. **Given** a run whose transcripts are missing or do not reconcile, **When** it ends, **Then** it is
   not counted, with the reason, and is rerun within the bound.

---

### User Story 3 - The decision carries its measurement (Priority: P2)

The owner deciding whether to release reads, in the README, the remeasure beside 001's eval and
either a release or a second "measured and not adopted" with its reason, and finds the run outputs
it rests on committed in the repository.

**Why this priority**: constitution III makes a passing eval the condition of release and a failed
one a recorded alternative; this story is that record.

**Independent Test**: the README holds an entry headed `Eval 002, <date>` with every field FR-009
lists; the run outputs are committed under `tests/eval/results/002-large-phase-remeasure/`; and the
outcome agrees with `preset.yml`, the CHANGELOG and the tags. `<date>` is the day the last counted run
ended, or for an eval that stopped without a verdict, the day it stopped.

**Acceptance Scenarios**:

1. **Given** every run counted, **When** every success criterion SC-001 to SC-008 holds, **Then** the
   README records the result and its top status line names the release; `preset.yml` keeps version
   `0.1.0` (the first release, a rule added: constitution V's MINOR) and its pre-release comment is
   replaced by one naming the release; `CHANGELOG.md` is created in Keep a Changelog form with its
   `0.1.0` entry; and the release is tagged `v0.1.0`.
2. **Given** every run counted, **When** any success criterion does not hold, **Then** no release is
   made: the README records the remeasure as measured and not adopted, naming each criterion that
   failed, its measured value against its threshold, and what the attribution shows about where the
   `with` arm's usage went; the README's top status line, `preset.yml`'s pre-release comment and the
   project `CLAUDE.md`'s description name both measurements; the measured state is tagged
   `measured-not-adopted-002-<date>`.
3. **Given** a run that does not count, **When** it has been rerun twice without counting, **Then**
   the eval stops and is recorded as not measured (scenario 6).
4. **Given** an arm's set of counted runs about to start, **When** the harness is ready, **Then**
   the owner has confirmed that set, shown in dollars the usage spent so far on this eval, the set's
   estimate and its worst case with every rerun (FR-008). The `with` and `fallback` sets alternate,
   so both are confirmed before either starts.
5. **Given** a third `without` set that misses no held-out test, **When** the eval stops, **Then** it
   is recorded as not measured (scenario 6), the reason being that the fixture had no headroom after
   two hardenings, with the three sets' results.
6. **Given** the eval stops without a verdict — a red probe, reruns exhausted, a third closed gate, or
   the owner stopping it — **When** it is recorded, **Then** the README holds an entry `Eval 002,
   <date>` (the day the eval stopped) saying not measured and why, with every field of FR-009 that
   exists; its top status line, `preset.yml`'s pre-release comment and the project `CLAUDE.md`'s
   description say 002 was not measured; every attempt's outputs are committed
   (FR-012); no release is made and no tag is created.

---

7. **Given** the eval stopped without showing the claimed effect, **When** the owner accepts the
   preset anyway (constitution III, v2.0.0), **Then** the README records the eval as it came out,
   never as a pass, beside the owner's decision, its reason and date; the release follows scenario
   1, its CHANGELOG entry linking the decision; and US4 follows.

### User Story 4 - The owner's setup adopts a released preset (Priority: P3)

Only after a release (scenario 1, or scenario 7), the owner's setup adopts the preset (FR-010). 001 specified these steps and
never carried them out, because 001 was not adopted.

**Why this priority**: it reaches projects only after User Story 3 passes; on a failure it does not
happen.

**Independent Test**: `sdd-init` in a scratch repository installs both presets; the dotfiles check
for `sdd-init` goes red when the story-workers preset is removed from it; `docs/claude-settings.md`
names the worker's effort as the exception and links decision 0001; each existing Spec Kit project
the owner approves has the preset in a commit of its own.

**Acceptance Scenarios**:

1. **Given** a release, **When** `sdd-init` runs in a new repository, **Then** it installs
   `constitution-authoring` and `story-workers` in its one commit.
2. **Given** no release, **When** this feature closes, **Then** nothing in the owner's setup changes.

### Edge Cases

- **Core passes every held-out test on the new fixture too**: no `without` run missed one, so the
  fixture has not met User Story 1; `with` and `fallback` do not run, the fixture is hardened, and
  `without` runs again, at most twice (FR-003); a third such set ends the eval (US3 scenario 5).
- **Claude Code or Spec Kit moved since 001**: the probes run first on the new version; a red probe
  stops the eval before any run, since the design rests on what they check.
- **Claude Code updates itself during the eval**: the runs' `versions.txt` would differ, and a
  comparison across them is refused. The harness disables the auto-updater for its runs and for the
  probes; before each try it checks the installed Claude Code version against the attempt's probes
  and the try's versions against the first counted `without` run's, refusing the try (nothing spent)
  on a difference; the eval then restarts on one version, in a new attempt. Keys only the run itself reveals (output
  style, plugins, MCP servers, skills) are compared after it, and a difference makes it not counted.
- **A `with` run carries a phase out in the main session** (fix hand-offs exhausted, a worker
  error): the run counts, and SC-003's `Carried out in this session: none` clause fails on it, which
  fails SC-003 (per-run, FR-011).
- **Runs per arm disagree** (one passes the threshold, another does not): the median decides, and
  the README shows every run, so a split result is visible rather than averaged away.
- **A run exceeds the agent's deadline**: it is not counted. The deadline is part of the harness's
  commit, so raising it changes every later run's `versions.txt`; raising it therefore discards every
  run counted before, and the eval restarts at the `without` set under the owner's confirmation. The
  README says so. It is never raised for one arm. Any other harness change during the eval does the
  same.
- **The harness itself faults during a run** (a bug in its own code, not the agent): the run is
  stopped as refused, kept for diagnosis, the harness is fixed in a commit, and the eval restarts at
  the `without` set; such a run neither counts nor uses a rerun.
- **A run's held-out tests fail to collect or error**: the score counts passed tests out of the fixed
  number of tests in the fixture's held-out suite; an error or an uncollected test is not passed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A second fixture MUST be committed under `tests/` beside 001's, with a setup phase and
  exactly three user-story phases of 6 to 10 task lines each (test-writing tasks included), a spec, a
  plan fixing the interface the held-out tests use, a `CLAUDE.md` that is 001's fixture's with only
  the project's name, one-line description and spec path changed (the same Commands, the same two
  conventions word for word: the `fixture:` commit prefix and a fresh `general-purpose` review per
  story), and no `checklists/` directory. The feature spec's stories are headed `### User Story <n> -
  <title> (Priority: P<n>)`, as 001's are, because the harness counts them. A hardening that would take a phase past
  10 tasks splits the added work into a new task in a phase under 10, or is not made.
- **FR-002**: The new fixture's held-out tests MUST cover each acceptance scenario of its spec at
  least once; each MUST name its scenario and quote the spec text its expected values follow from
  (US1 scenario 2), and MUST all pass against a reference implementation kept outside what the agent
  sees. The fixture's difficulty MUST come only from: (a) rules the spec states that interact, (b)
  edge cases the spec states as acceptance scenarios, (c) phases whose tasks span three or more
  modules. A requirement is ambiguous when two readings of the spec text give different expected
  values for a held-out test; no held-out test may rest on one. Before any run, a review in a fresh
  context checks every held-out test against its quoted text, applying this ambiguity test and the
  closed list above; its findings, and how each was resolved, are recorded in
  `specs/002-large-phase-remeasure/heldout-review.md`; a finding is closed when a fresh-context review
  of the changed test finds it settled, or finds the recorded reason for leaving the test unchanged
  sound; and every finding is closed before the `without` set starts. A hardening repeats the review for what it
  adds, and the oracle proof for the whole held-out suite, before its `without` set.
- **FR-003**: The `without` arm's counted runs MUST run first, and `with` and `fallback` MUST NOT run
  on the fixture until at least one `without` run misses at least one held-out test. The fixture MAY
  be hardened at most twice for this; a hardened fixture discards every earlier `without` run.
- **FR-004**: The harness MUST run either fixture, chosen per run, with everything else about the
  arms as in 001 (hermetic isolation, the same allowed tools, the main session's model and effort,
  the counting rules of 001's FR-011, the comparison refused on a versions mismatch), with Claude
  Code's auto-updater disabled for its runs and the probes, and with a run's versions checked against
  a baseline run's before the agent starts.
- **FR-005**: The usage output MUST carry what US2 lists: per model, input, output, cache-read,
  5-minute and 1-hour cache-write tokens and cost and their sum; per subagent its part (worker,
  review, other) and, for `with`, its phase; for `with`, the main session's `before`, per-phase,
  `after` and `unattributed` parts as US2 scenario 2 defines them; for `without` and `fallback`, the
  main session as one part.
- **FR-006**: The fragment MUST be 001's as merged, unchanged; the README names the commit measured.
- **FR-007**: The eval MUST run `without`, `with` and `fallback`, three counted runs each, in the order
  `without` ×3, then `with` and `fallback` alternating, judged on each arm's median, with every run
  and its spread in the README.
- **FR-008**: Each arm's set of counted runs MUST start only after the owner confirms it, shown in
  dollars: the cost spent so far on this eval — every try, counted, not counted or discarded, priced
  from its `result` event's `costUSD` or, for a try without one (killed at the deadline), from its
  transcripts at the price table; the set's estimate — three times the highest counted run cost on
  this fixture in any of its hardenings for that arm; for an arm with no counted run yet, three runs
  at twice the highest counted run cost of any arm (provisional: 001's `with` run cost 1.65 times its
  `without` run); before any run has counted, three runs at 001's `without` run cost scaled by the
  ratio of the fixtures' task counts (unmeasured, and labelled so) — summed over the sets confirmed
  together; and its worst case, three times the estimate (every run rerun twice).
  The spend covers every headless Claude Code invocation of the eval, probes included; a try with no
  cost recorded (refused before the agent, a failed setup, a probe killed at its deadline) counts as
  zero. Reruns of a run that
  did not count need no new confirmation.
- **FR-009**: The README MUST record, beside 001's entry (which stays as it is): the date; the fixture
  and its size (stories, tasks per phase, held-out tests); the commit measured; the arms and run
  order; every run's total and per-model cost, held-out score and suite result, with each arm's median
  and spread, and that three runs bound what can be said about variance; every run that did not count,
  with its reason; the gate's history (every `without` set run, with its misses) and any hardening,
  with what it added; every attempt discarded for a harness fault or a version change, with its
  reason; any deadline change; the attribution of US2 for every counted run; the probes;
  the isolation; the versions of every tool and model; the success criteria with their values; and a
  reading. The comparison and the reading are within this feature's runs; 001's numbers may be cited
  only as context, labelled as another fixture.
- **FR-010**: On a release, the owner's setup MUST adopt the preset: dotfiles' `sdd-init` installs it
  beside `constitution-authoring`, with its check seen red when it is removed; dotfiles'
  `docs/claude-settings.md` names the worker's effort as the one exception to its effort policy and
  links decision 0001; each existing Spec Kit project gets the preset only with the owner's approval,
  in a commit of its own. On no release, nothing outside this repository changes.
- **FR-011**: SC-003, SC-005 and SC-007 MUST hold on every counted run of their arm; SC-004 MUST hold
  once on the measured commit with the Spec Kit version the eval ran on; SC-006 MUST hold once on the
  Claude Code version every counted run ran on (the version in the probes' output equals every run's
  `versions.txt`).
- **FR-012**: Every attempt's outputs MUST be committed under
  `tests/eval/results/002-large-phase-remeasure/attempt-<k>/`, discarded attempts included: every
  counted run's files as 001's were (`status`, `usage.txt`, `usage.json`, held-out, suite, versions,
  models, commits, report and, for `with`, attribution), every other try's `status` (refused tries
  included), the probes' output, the gate's output,
  and, for the attempt that reached a verdict, the comparison's output and SC-004's; streams and
  transcripts are not committed, since they carry local paths and session ids.
- **FR-013**: The `with` main session's spans MUST be computed from its transcript in turn order, a
  turn being one assistant message (its transcript entries merged by `message.id`). A phase *n*'s
  start is the first turn holding a worker call — an Agent call with `model: "sonnet"` — whose
  prompt's first line is phase *n*'s heading in the fixture's `tasks.md` (heading and emphasis marks
  aside, as SC-003 compares them); its
  marking is the first turn holding a Bash call whose command commits with a message containing
  `tasks: mark phase <n>`, `<n>` being the number in that phase's heading (`## Phase <n>: …`; the
  fixture numbers its phases from 1 in order), and whose result reports no error. When for every phase, in order,
  start₁ ≤ marking₁ < start₂ ≤ marking₂ < … ≤ markingₖ: `before` is every turn before start₁; phase
  1 is start₁ through marking₁; phase *n* > 1 is the turn after markingₙ₋₁ through markingₙ; `after` is
  every turn after markingₖ. The order breaks at the first phase *n* whose start or marking is missing,
  or with startₙ > markingₙ, or with markingₙ ≥ startₙ₊₁ (the next phase handed off before this one
  was marked); from there, every turn from the turn after the last well-formed marking to the end — every
  turn of the session when phase 1 breaks, `before` included — is `unattributed`, and there is no
  `after`.

### Key Entities

- **Fixture**: a committed Spec Kit feature (spec, plan, tasks, project instructions) in a small
  project, plus its held-out tests and a reference implementation the agent never sees.
- **Eval run**: one try of one arm on one fixture, counted or not, with its outputs.
- **Usage attribution**: a run's tokens and cost per model, split into parts (main session or its
  phases, workers, reviews, other subagents), reconciled with what Claude Code reported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the new fixture, the `with` arm's median total cost — every model's, verification and
  reviews included — is at least 30% below the `without` arm's median: `1 - with / without >= 0.30`.
- **SC-002**: On the new fixture, `with`'s median held-out score is at least `without`'s, and `with`'s
  own suite is green at the end of every counted run.
- **SC-003**, **SC-005**, **SC-007**: 001's SC-003, SC-005 and SC-007, on the new fixture, holding on
  every counted run of their arm (FR-011); SC-005's held-out clause compares `fallback`'s median score
  with `without`'s.
- **SC-004**: 001's SC-004, re-observed on the measured commit with the eval's Spec Kit version: the
  composition test goes red when any core rule FR-008 of 001 names, or core step the brief names, is
  removed from the **core** `speckit-implement` skill before the preset is added (the fragment itself
  quotes every anchor, so the composed skill would always carry them).
- **SC-006**: every probe passes, on the Claude Code version of every counted run (FR-011).
- **SC-008**: Every counted run's usage is reconciled: per model and per token type, the sum over its
  transcripts equals what Claude Code reported, and the cost priced from those tokens equals the
  reported cost within $0.000001; and its parts' tokens sum exactly to those totals and their cost to
  the reported cost within $0.000001. (Runs that do not
  reconcile do not count, US2 scenario 4; SC-008 guards that no counted run escapes the check.)

## Assumptions

- The arms, isolation, counting rules, probes and versions file are 001's (its research.md R6); this
  feature changes the fixture, the usage output, the choice of fixture per run, the auto-updater, and
  adds reconciliation to counting.
- The main session stays Opus at `--effort medium` and the worker Sonnet at `effort: "medium"`
  (decision 0001); another pairing is not measured.
- Cost is the per-model `costUSD` Claude Code reports for a headless run, at list price. The per-turn
  usage comes from Claude Code's session transcripts, an internal format, not a published interface:
  observed on 2026-10-14 to reconcile exactly with `costUSD` (research.md R1), and checked on every run
  (SC-008) because it may change.
- One synthetic fixture, however large, is less representative than a real feature; the README says
  so, as in 001.
