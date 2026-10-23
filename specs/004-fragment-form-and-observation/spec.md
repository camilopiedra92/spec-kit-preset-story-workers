# Feature Specification: Fragment form, and observed verification

**Feature Branch**: `004-fragment-form-and-observation`

**Created**: 2026-10-23

**Status**: Draft. The behaviour of the rewritten fragment is NOT measured (see "Evals: plan and
budget"); this line is replaced by the results when E1 to E3 are recorded.

**Input**: An outside review of the text the Spec Kit presets add (owner-commissioned, 2026-10-22,
kept outside this repository) found the story-workers fragment's form harder to follow than its
substance deserves, and its verification resting on the worker's report. The owner, on 2026-10-23:
do not defer the rewrite of the fragment, and measure it.

## Context

`docs/decisions/0005` (2026-10-22) made two changes without an eval and deferred three. Its reason
for deferring ("the owner declined to spend usage on evals") was **a misreading by the orchestrating
session, not an owner decision**: the owner's refusal to pay concerned GitHub Actions only, and model
usage from his subscription for evals is approved (2026-10-23). The deferral is withdrawn, 0005 is
superseded by this feature, and constitution III is met the proper way: the changes ship with evals
(US3), recorded as they come out.

Of 0005's three deferred items, two are this feature's stories. The third (a composition test with
another preset that appends to `speckit-implement`) stays moot: the only other such preset,
spec-kit-preset-test-first, was archived on 2026-10-08.

## Clarifications

### Session 2026-10-23 (owner)

- Q: Defer the form rewrite? A: No; implement it.
- Q: May evals run? A: Yes. Model usage from his subscription is approved; only GitHub Actions spend
  is refused. The statement that he declined to spend on evals is withdrawn everywhere it was
  recorded (0005, the CHANGELOG entry for the #7 paragraph; PR #7's body is already corrected).
- Q: Release? A: Not decided. Nothing is tagged, `preset.yml` stays `0.2.0`, entries stay under
  `[Unreleased]`; the owner decides after reading the measured results. A result that shows a change
  makes things worse is reported as it is.
- Q: Which harness? A: the repo's own (fixture `checkout`, `tests/eval/run.sh`, three counted runs
  per arm, versions recorded), extended only where a claim cannot be judged without it (US3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The fragment's rules read one per bullet (Priority: P1)

A model following `## Story workers` meets each rule as its own short bullet, not as one clause of a
fourteen-line sentence, and the rationale sits in the README. **No rule is added, removed, reordered
or reworded in meaning.**

**Why this priority**: the review's largest finding (form); and a form change is where a rule is
most easily lost without anyone noticing, so it is made checkable.

**Independent Test**: the rule inventory below (R1 to R88, taken from the fragment at `53059f8`)
maps one to one onto the new bullets (`plan.md`, "Mapping"); `tests/fragment_rules.py`, run by
`tests/compose.sh` against the composed skill, fails on a bullet missing, duplicated, extra or
changed, and on an inventory row without a bullet. That the new text *means* what the old did is
**not automatable**: a fresh-context reviewer compares the inventory with the old and the new text.
That is the check for equivalence, and the owner runs it.

**Acceptance Scenarios**:

1. **Given** the inventory and the mapping, **When** the test runs on the composed skill, **Then**
   every `Rn` is carried by exactly one bullet (or the one paragraph), every bullet by one `Rn`, and
   nothing is unmapped on either side.
2. **Given** a bullet removed or duplicated by hand, **When** the test runs, **Then** it fails,
   naming the rule.
3. **Given** the composed skill, **When** `core-anchors.sh` and `compose.sh`'s phrases run, **Then**
   they pass (a phrase the new form moves is listed in `plan.md`).
4. **Given** the six justification sentences (J1 to J6), **When** the README is read, **Then** each
   is there under its id.

### User Story 2 - The main session observes, it does not believe (Priority: P2)

Today the line `Carried out in this session: none` or with ids, the "found already done" tasks and
the worker's list of commits rest on the worker's report. The main session observes them with what
it can already run: `git`.

**Why this priority**: a **new rule** (it adds behaviour): it ships unreleased and unmeasured until
US3's evals say what it does.

**Independent Test**: anchors on the composed text (`compose.sh` phrases for each new bullet) and a
deterministic stand-in: the commands the new bullets name are run, placeholders substituted, in
`compose.sh`'s scratch git repository, and must tell a worker's range from an earlier commit, an
empty range from a non-empty one, and a tracked file from an untracked one. Seen red with each
command altered by hand.

**Acceptance Scenarios**:

1. **Given** a recorded HEAD and two commits after it, **When** the bullet's `git rev-list --count`
   and `git log` run, **Then** they report 2 and those two commits.
2. **Given** a commit made before the recorded HEAD, **When** `git merge-base --is-ancestor <commit>
   <recorded HEAD>` runs, **Then** it succeeds; for a commit made after it, it fails.
3. **Given** a tracked and an untracked file, **When** `git ls-files --error-unmatch <file>` runs,
   **Then** it succeeds only for the tracked one.
4. **Given** the composed skill, **When** the anchors run, **Then** each new bullet is present.

### User Story 3 - The changes ship with their measurement (Priority: P1)

Constitution III: a rule added, changed or dropped ships with an eval. Three comparisons, each the
preset with and without the change, on the repo's fixture, three counted runs per arm, versions
recorded, written in the README with date and what was compared as they come out:

- **E1** (US1): the fragment before (`53059f8`) against the rewritten one.
- **E2** (US2): the rewritten fragment against it plus the observation rules.
- **E3** (the paragraph #7 merged on 2026-10-23, never measured): `v0.2.0` against `53059f8`, in a
  project that is not a git repository.

**Independent Test**: the README holds one entry per comparison; the CHANGELOG entries link them and
stay under `[Unreleased]`.

## Requirements *(mandatory)*

- **FR-001**: Each normative statement of the fragment at `53059f8` MUST be inventoried (`Rn`, line,
  verbatim) before the rewrite, and the rewrite MUST map each to exactly one bullet (or the one
  paragraph) and each bullet to exactly one `Rn`.
- **FR-002**: The rewrite MUST NOT add, remove, reorder or reword in meaning any inventoried rule.
  Sentences that justify a rule rather than state one (J1 to J6) move to the README under their ids.
- **FR-003**: A test MUST read the inventory and the mapping and fail when the composed skill's
  fragment differs from the mapping, or the inventory from the mapping's ids; it MUST be seen red
  before the rewrite and with a bullet removed and duplicated by hand.
- **FR-004**: The observation rules (N1 to N5 below) MUST use only commands the main session can
  already run, MUST say what happens when the report and the observation disagree (verification
  fails, as any failed verification does), and MUST NOT add a stop or a question (constitution IV).
- **FR-005**: Every place that says the owner declined to spend on evals MUST be corrected as a
  misreading.
- **FR-006**: The evals MUST run on the repo's harness; any change to it MUST be tested and seen red.
- **FR-007**: Nothing is tagged or released, `preset.yml` stays `0.2.0`, entries stay under
  `[Unreleased]`; the specs, PRs, CHANGELOG and README say that the behaviour of the rewritten
  fragment was not measured until E1 to E3 are recorded, and then say what they showed.

### New rules (US2), N1 to N5

| Id | Statement (as it will read in the fragment) |
|---|---|
| N1 | Record HEAD before each worker, a fix hand-off's included, not only each phase's first. |
| N2 | When a worker returns, run `git rev-list --count <recorded HEAD>..HEAD` and `git log --format='%h %s' <recorded HEAD>..HEAD`: the commits in that range are the worker's work, whatever its report says. |
| N3 | A report that lists tasks done while that range is empty, or whose first or last commit is not the range's, fails verification and goes to a worker as any failed verification does. |
| N4 | Mark a task the worker found already done only if the commit its report cites passes `git merge-base --is-ancestor <commit> <recorded HEAD>` or the file it cites passes `git ls-files --error-unmatch <file>`. |
| N5 | Write the `Carried out in this session:` line from this observation, not from a worker's report: `none` only when every commit of `git rev-list <first recorded HEAD>..HEAD` is in a worker's range, one of the run's `tasks:` commits or a commit of core's extension hooks; otherwise list the tasks the other commits and edits cover. |

**What these do not establish.** They show that the report and the repository agree on commits and
cited evidence. They do not show the worker's code is right (the suite and the review do), that a
model follows them (only an eval can), or that a mistaken or dishonest report is caught more often
than before: the eval's workers are not told to misreport, so E2 can show that the main session ran
the commands and whether doing so cost or broke anything, not that it caught a misreport. `git` can
say when a commit was made, not who made it: work by the user in the same worktree during a
foreground worker's interval would read as the worker's.

## Success Criteria *(mandatory)*

- **SC-001** (US1): `tests/fragment_rules.py` green on the composed skill, red with a bullet removed,
  one duplicated and an inventory row dropped, each seen. The reviewer's equivalence check: pending
  (the owner).
- **SC-002** (US2): the stand-in green; red with each command altered; the anchors green.
- **SC-003** (US3): E1 to E3 recorded with date, arms, runs, versions, cost, and the result as it
  came out.

## Evals: plan and budget

Harness: `tests/eval/run.sh` with `--preset <ref>` (an arm's fragment from a commit), fixture
`checkout`, state `phase-2-done-doc-task` (a feature resumed at Phase 3, with a task the main session
carries out itself, so the `Carried out in this session:` line has something to say) for E1 and E2;
`checkout` fresh for E3, with a new `--no-git` flag (the run's `.git` is moved aside while the agent
runs, as in a contained run's export of a project). `runs.sh` is not used: its gate belongs to Eval
002's without/with question and these arms are all `with`. Each arm gets three counted runs, arms
alternating, each run tried at most three times (a try counts once it left a stream). Judged by
`resume_check.py` (its nine checks), `observe_check.py` (new, E2) and `nogit_check.py` (new, E3). The
probes run first (`tests/eval/probes.sh`).

| Comparison | Arms | Runs | About per run (earlier evals) | Estimate | Worst case (+30% reruns) |
|---|---|---|---|---|---|
| probes | | 14 probes | | $1.4 | $1.4 |
| E1, E2 | A `53059f8`, B US1, C US2 | 3 x 3 = 9 | $1.9 to $2.3 (Eval 003, `doc-1` $1.91) | $18 | $27 |
| E3 | `v0.2.0`, `53059f8` | 2 x 3 = 6 | $1.8 to $2.3 (Evals 001 and 002) | $12 | $18 |
| **Total** | | 15 | | **about $31** | **about $46** |

Nothing is a gate: each result is recorded as it comes out. What would count against a change,
stated in advance: in E1, B failing a check A passes in the same state; in E2, C failing a check B
passes, or the main session not running the observation (no `git log` range after a worker returns);
in E3, the `53059f8` arm starting a worker in a project with no git, or not saying why it did not.
Cost differences are reported; with three runs they are directional.

**Not established by these evals, whatever they show**: that the rewrite's expected compliance gain
exists in general (one fixture, one model pair, three runs); anything about a real project's
features; that the observation catches a misreport (see above); the fragment on any agent but Claude
Code. When this spec was written they had not been run.

## Rule inventory (US1, FR-001)

Taken on 2026-10-23 from `commands/speckit.implement.md` at `53059f8` (110 lines), before any edit.
One row per normative statement: an instruction to the main session or the worker, a condition, an
exception, a form the completion report takes, or the naming of a core rule narrowed. `Line` is the
line of the file where the statement starts. `Statement` is a verbatim span of the file (whitespace
squeezed; `...` joins two spans of one statement). Removing every span here and in the justification
table below from the file's text leaves only connectives and the section labels (checked by script,
2026-10-23). Rows are in the order of the file; the new text keeps that order.

| Id | Line | Statement, verbatim from the current fragment |
|---|---|---|
| R1 | 3 | In a project that is not a git repository, such as an export of one without its `.git`, **The call** sends the run to **Fallback**: the remaining tasks are carried out in this session as core does, and the completion report says which and why. |
| R2 | 7 | This section narrows the steps above: where it and they differ, it applies. |
| R3 | 7 | You are the main session. You hand each phase to a worker, verify it in your own runs, decide, and keep `tasks.md` |
| R4 | 9 | the workers write the code |
| R5 | 11 | Hand each phase to a worker: one worker per phase of `tasks.md` |
| R6 | 11 | in the order the steps above run the phases, the next only after the previous one's verification |
| R7 | 12 | never two at once |
| R8 | 13 | This narrows core's "parallel tasks [P] can run together": `[P]` tasks run inside their phase's worker, one after another |
| R9 | 16 | Start each worker with the Agent tool, `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"` and `run_in_background: false` |
| R10 | 18 | With no Agent tool, when the call returns an error, or when the project is not a git repository … go to **Fallback** below: core's own behaviour |
| R11 | 22 | It opens with the phase's heading as `tasks.md` writes it |
| R12 | 22 | the phase's unmarked tasks … or, for a fix, the finding |
| R13 | 23 | which may already be done, in whole or in part (check each against the code and `git log`, and complete only what is missing) |
| R14 | 24 | the feature directory; |
| R15 | 24 | the suite and static-check commands, from the project's instructions, else `plan.md`'s Technical Context |
| R16 | 26 | and the phases already marked |
| R17 | 26 | It tells the worker to follow core's "Load and analyze the implementation context", "Project Setup Verification" (Phase 1's worker only), "Execute implementation", "Implementation execution rules" and "Progress tracking and error handling" steps of `.claude/skills/speckit-implement/SKILL.md`, whose Story workers section is the main session's, not the worker's |
| R18 | 30 | that the worker commits each task in a commit of its own, staging only the files it changed, never `git add -A` or `-a` |
| R19 | 31 | that it commits what Project Setup Verification changes in a commit of its own |
| R20 | 32 | and adds to the project's ignore file, in a commit of its own, any file the suite or the static checks generate that git does not ignore |
| R21 | 33 | that it never edits, stages, commits or reverts a file in the feature directory, and leaves a task that needs one unfinished, saying so |
| R22 | 35 | that it follows a call a project hook blocks, or leaves that task unfinished with the hook's message in its report |
| R23 | 36 | and that it does not edit `tasks.md` (core's "mark the task off as [X]" in those steps is yours) |
| R24 | 37 | start a review |
| R25 | 37 | start another worker |
| R26 | 39 | the first and last commit |
| R27 | 39 | the tasks done |
| R28 | 39 | the tasks found already done, with the commit or file that holds each |
| R29 | 40 | for each task not done, what stopped it |
| R30 | 41 | anything found that no task covers |
| R31 | 41 | the output of its last whole-suite run |
| R32 | 43 | Before a phase's first worker, record HEAD and run the static checks: that is the baseline |
| R33 | 44 | This narrows core's "For completed tasks, make sure to mark the task off as [X]": the main session marks a task [X] only after its own runs show the whole suite passing and no static-check finding the baseline lacked |
| R34 | 46 | its reading of the commits made since the recorded HEAD finds nothing the phase's tasks do not call for |
| R35 | 47 | and `git status --porcelain --untracked-files=all`, run before its own suite and static-check runs, lists nothing outside the feature directory |
| R36 | 48 | (what it lists is the worker's, and goes back to it as a finding) |
| R37 | 49 | a task the worker found already done is marked on the suite, the static checks and its reading of the commit or file the worker cites |
| R38 | 50 | Run what the project names |
| R39 | 51 | say in the completion report what it does not name |
| R40 | 51 | A worker's report never marks a task |
| R41 | 52 | A review the phase calls for, and its fixes, resolve first |
| R42 | 52 | then commit `tasks.md` with a message containing `tasks: mark phase <n>` (after any prefix the project's instructions require; |
| R43 | 54 | none when the phase marked nothing new) |
| R44 | 54 | and only then start the next phase's worker |
| R45 | 56 | This narrows core's "Halt execution if any non-parallel task fails": every unfinished task … failed verification or review finding goes to a worker briefed with it, then verification again |
| R46 | 57 | (except one that changes the feature directory, which this session carries out, as **A clean tree outside the feature** says) |
| R47 | 59 | a review finding passes when a fresh review of it no longer reports it |
| R48 | 60 | A phase gets at most two fix hand-offs |
| R49 | 60 | every hand-off after its first counting, whatever items it carries |
| R50 | 61 | when verification still fails after them (a fresh review still reporting its finding included), carry out the phase's remaining items in this session as core does |
| R51 | 62 | Tasks a worker reports finding join the current phase in `tasks.md` |
| R52 | 63 | committed with a message containing `tasks: add found tasks` |
| R53 | 64 | go to its next hand-off |
| R54 | 64 | Outside the items this session carries out, your only edits to tracked files are `tasks.md` (checkboxes, found tasks) and its commits |
| R55 | 65 | running the suite, the static checks or core's extension hooks is not writing code |
| R56 | 68 | Start any review the user's or the project's instructions, or a command, call for in a fresh context: `subagent_type: "general-purpose"`, with `model` set to this session's model family (for example `opus`) and no `effort` |
| R57 | 70 | Never in a worker |
| R58 | 71 | Where no fresh context can be started, the review does not run and the completion report says so |
| R59 | 74 | A call a project hook blocks is the worker's to follow or report |
| R60 | 74 | never make it yourself, in the fallback too |
| R61 | 75 | Such a task is not handed off again |
| R62 | 75 | it stays unmarked, goes into the completion report |
| R63 | 76 | and the next phase starts without it |
| R64 | 76 | unless the suite is red because of it, in which case core's "Halt execution if any non-parallel task fails" applies and the run ends with the report |
| R65 | 80 | When no worker can carry on (no Agent tool, a worker's error, a usage limit included, a missing report, a project that is not a git repository, or uncommitted changes outside the feature directory when the run starts), carry out the remaining tasks in this session as core does |
| R66 | 82 | and say which and why in the completion report |
| R67 | 83 | The bound of two fix hand-offs is narrower: it moves only that phase's remaining items into this session, and the next phase goes to a worker as usual |
| R68 | 84 | The completion report always carries the line `Carried out in this session: none`, or `Carried out in this session:` followed by the task ids and, for fix items, the phase and a short name of each |
| R69 | 88 | `tasks.md`'s marks, `[X]` or `[x]`, read from the file as core reads it, are the record of what is done, whoever made them |
| R70 | 89 | where a run starts is never read from commit messages |
| R71 | 90 | A run takes the phases in order and skips every phase whose tasks are all marked, wherever it falls |
| R72 | 91 | it starts at the first phase with an unmarked task, at Phase 1 when none is marked |
| R73 | 91 | When every task is marked, start no worker, commit nothing |
| R74 | 92 | and say so in the completion report in place of the line below |
| R75 | 93 | Each phase's baseline is taken as Verification says |
| R76 | 93 | Work committed before the run is covered by the whole-suite run only |
| R77 | 94 | When a phase went to a worker, the completion report carries the line `Started at phase <n>: work committed before this run was covered by the whole suite, not read as a diff, its static-check findings in the baseline.` |
| R78 | 98 | Before the first worker and before any of the run's own suite or static-check runs, run `git status --porcelain --untracked-files=all` |
| R79 | 99 | When it lists a path outside the feature directory, a worker's changes could not be kept apart from that work: carry out the run in this session as core does (**Fallback**) |
| R80 | 101 | and name those paths in the completion report |
| R81 | 102 | Inside the feature directory, uncommitted changes stay as they are: the run neither asks about them nor stops for them |
| R82 | 103 | they are not a finding |
| R83 | 103 | and no worker edits, stages, commits or reverts a file there |
| R84 | 104 | Commits that core's extension hooks make are core's, not the run's |
| R85 | 104 | The run's `tasks: mark phase` and `tasks: add found tasks` commits carry `tasks.md` as it stands, its earlier edits included |
| R86 | 106 | A task that changes a file in the feature directory is carried out in this session as core does, all of it |
| R87 | 107 | its files in the feature directory are left uncommitted, as core leaves them |
| R88 | 108 | What this session changes outside the feature directory while carrying out items, it commits as soon as it has carried them out, before any later Verification or worker, in a commit whose message contains `tasks: carried out in this session` |

## Justification sentences (US1, FR-002)

Sentences that explain a rule rather than state one. They leave the fragment and go to the README
under their ids (a reader of the fragment loses nothing it must do). Each was read twice for a rule
hidden in it: "(the commits, diffs and baseline below need git)" restates R10's reason and adds no
condition; the others give a reason only.

| Id | Line | Sentence, verbatim | Moves to |
|---|---|---|---|
| J1 | 14 | since two workers would write the same worktree and index | README, "Why the fragment's rules read as they do" |
| J2 | 17 | so its report is in hand before you verify | README, "Why the fragment's rules read as they do" |
| J3 | 19 | (the commits, diffs and baseline below need git) | README, "Why the fragment's rules read as they do" |
| J4 | 70 | so it thinks as hard as this session | README, "Why the fragment's rules read as they do" |
| J5 | 72 | a review by the context that wrote the code is not one | README, "Why the fragment's rules read as they do" |
| J6 | 100 | a worker's changes could not be kept apart from that work | README, "Why the fragment's rules read as they do" |
