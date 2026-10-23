# Implementation Plan: Fragment form, and observed verification

**Branch**: `004-fragment-form-and-observation` (stacked PRs, one per step: spec, harness, US1, US2,
results) | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

## Summary

Rewrite `## Story workers` as one rule per bullet with the rationale in the README, provably
without adding, removing, reordering or rewording a rule (inventory in the spec, mapping below, a
test that compares them to the composed skill); add five observation rules that make the main
session check the worker's report against `git`; then measure both changes, and the already merged
#7 paragraph, with the repo's own eval harness. Unreleased throughout: no tag, no version bump.

## Technical Context

**Language/Version**: Markdown (the fragment); bash (`compose.sh`, `run.sh`); Python 3.11+
(`tests/fragment_rules.py`, `tests/eval/observe_check.py`, `tests/eval/nogit_check.py`).

**Primary Dependencies**: as 003: Spec Kit CLI 1.2.2 locally (pinned 1.1.0 in CI), Claude Code, jq,
git; dev ruff, mypy, pytest.

**Testing**: `tests/check.sh` once per story close. New: `tests/fragment_rules.py` (called by
`compose.sh` on the composed skill, with its own red checks there), `compose.sh` phrases and the
observation stand-in, `test_observe_check.py`, `test_nogit_check.py`, `test_run.py` for `--no-git`.
The evals spend usage (spec, "Evals: plan and budget").

**Constraints**: constitution I (still appended, narrowed rules still named, `core-anchors.sh`
unchanged), III (evals), IV (no new stop or question), V (no release; the archive allowlist is
unchanged: `tests/` and `specs/` are export-ignore).

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Append, never replace | The fragment stays appended without frontmatter; the three narrowed core rules are still named verbatim (phrases in `compose.sh`, anchors unchanged). |
| II. Real CLI | The new test runs on the skill the real `specify` composes. |
| III. Measured | US1 and US2 change rules' form and add rules; E1 to E3 measure them; results recorded as they come out; nothing released until the owner accepts. |
| IV. Degrades to core | N1 to N5 name no new capability beyond `git`, which the fragment already needs (R10); a project without git already goes to Fallback. |
| V. Released by tag | Nothing is tagged; `[Unreleased]` only. |

## Project Structure

```text
specs/004-fragment-form-and-observation/   spec, plan (the mapping), research, tasks
docs/decisions/0005-...                    superseded by this feature; its reason corrected
commands/speckit.implement.md              US1: bullets; US2: Observation section
tests/fragment_rules.py                    US1: inventory and mapping against the composed skill
tests/compose.sh                           calls it; its red checks; migrated phrases; N-phrases and stand-in
tests/eval/run.sh, test_run.py             --no-git (E3)
tests/eval/observe_check.py (+ test)       E2's check
tests/eval/nogit_check.py (+ test)         E3's check
README.md, CHANGELOG.md                    the rationale (J1 to J6); the eval entries; [Unreleased]
```

## Mapping (US1)

Each row is one block of the new fragment, in order. `Kind`: `H` the heading, `P` a paragraph that
carries one rule, `L` a label line (no rule), `B` a bullet that carries one rule. `Rule` is the
inventory id (spec, "Rule inventory"); `-` for `H` and `L`. `tests/fragment_rules.py` reads this
table. Every `Rn` appears once, every bullet and paragraph carries one, and the order of the ids is
the order of the current fragment's lines. The text is the bullet verbatim (the test compares it
with whitespace squeezed).

Decisions inside the mapping:

- A rule stated twice in the current text (the feature-directory exception in Hand-offs, and again
  in A clean tree) is two inventory rows, R46 and R86, because they are two statements.
- The `This narrows core's "..."` clauses stay attached to the first rule they govern (R8, R33,
  R45), as the constitution (I) requires the narrowed rule to be named in the fragment.
- R33 to R35 were one sentence with three conjunctive conditions for marking a task. Each is now
  its own bullet beginning "marks a task [X] only after", so each condition is a rule that can be
  followed or missed on its own; the conjunction is kept (all three still apply).
- R13's parenthesis was an instruction to the worker ("check each ... and complete only what is
  missing"); it stays an instruction, now introduced by "tells the worker".

### Phrases the new form moves in `tests/compose.sh`

Seven phrases of the fragment check change in capitalisation or in the clause they sit in; each
still states the same clause. They are edited in the same commit as the test and are red before the
rewrite (the old fragment lacks the new spelling):

| Was | Becomes |
|---|---|
| `where a run starts is never read from commit messages` | `Where a run starts is never read from commit messages` |
| `it starts at the first phase with an unmarked task, at Phase 1 when none is marked` | `It starts at the first phase with an unmarked task, at Phase 1 when none is marked` |
| `they are not a finding` | `They are not a finding` |
| `no worker edits, stages, commits or reverts a file there` | `No worker edits, stages, commits or reverts a file there` |
| `its files in the feature directory are left uncommitted, as core leaves them` | `Its files in the feature directory are left uncommitted, as core leaves them` |
| `and \`git status --porcelain --untracked-files=all\`, run before its own suite` | `\`git status --porcelain --untracked-files=all\`, run before its own suite` |
| `except one that changes the feature directory, which this session carries out` | `an unfinished task that changes the feature directory, which this session carries out` |

### The table

| Kind | Rule | New text, verbatim |
|---|---|---|
| H | - | ## Story workers |
| P | R1 | In a project that is not a git repository, such as an export of one without its `.git`, **The call** sends the run to **Fallback**: the remaining tasks are carried out in this session as core does, and the completion report says which and why. |
| B | R2 | This section narrows the steps above: where it and they differ, it applies. |
| B | R3 | You are the main session. You hand each phase to a worker, verify it in your own runs, decide, and keep `tasks.md`. |
| B | R4 | The workers write the code. |
| L | - | **Unit and order.** |
| B | R5 | Hand each phase to a worker: one worker per phase of `tasks.md`. |
| B | R6 | Take the phases in the order the steps above run them, the next only after the previous one's verification. |
| B | R7 | Never run two workers at once. |
| B | R8 | This narrows core's "parallel tasks [P] can run together": `[P]` tasks run inside their phase's worker, one after another. |
| L | - | **The call.** |
| B | R9 | Start each worker with the Agent tool, `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"` and `run_in_background: false`. |
| B | R10 | With no Agent tool, when the call returns an error, or when the project is not a git repository, go to **Fallback** below: core's own behaviour. |
| L | - | **The brief.** |
| B | R11 | The brief opens with the phase's heading as `tasks.md` writes it. |
| B | R12 | It carries the phase's unmarked tasks, or, for a fix, the finding. |
| B | R13 | It says the phase's unmarked tasks may already be done, in whole or in part, and tells the worker to check each against the code and `git log`, and to complete only what is missing. |
| B | R14 | It carries the feature directory. |
| B | R15 | It carries the suite and static-check commands, from the project's instructions, else `plan.md`'s Technical Context. |
| B | R16 | It carries the phases already marked. |
| L | - | It tells the worker: |
| B | R17 | To follow core's "Load and analyze the implementation context", "Project Setup Verification" (Phase 1's worker only), "Execute implementation", "Implementation execution rules" and "Progress tracking and error handling" steps of `.claude/skills/speckit-implement/SKILL.md`, whose Story workers section is the main session's, not the worker's. |
| B | R18 | That it commits each task in a commit of its own, staging only the files it changed, never `git add -A` or `-a`. |
| B | R19 | That it commits what Project Setup Verification changes in a commit of its own. |
| B | R20 | That it adds to the project's ignore file, in a commit of its own, any file the suite or the static checks generate that git does not ignore. |
| B | R21 | That it never edits, stages, commits or reverts a file in the feature directory, and leaves a task that needs one unfinished, saying so. |
| B | R22 | That it follows a call a project hook blocks, or leaves that task unfinished with the hook's message in its report. |
| B | R23 | That it does not edit `tasks.md` (core's "mark the task off as [X]" in those steps is yours). |
| B | R24 | That it does not start a review. |
| B | R25 | That it does not start another worker. |
| L | - | **The report** the brief asks for: |
| B | R26 | The first and last commit. |
| B | R27 | The tasks done. |
| B | R28 | The tasks found already done, with the commit or file that holds each. |
| B | R29 | For each task not done, what stopped it. |
| B | R30 | Anything found that no task covers. |
| B | R31 | The output of its last whole-suite run. |
| L | - | **Verification.** |
| B | R32 | Before a phase's first worker, record HEAD and run the static checks: that is the baseline. |
| B | R33 | This narrows core's "For completed tasks, make sure to mark the task off as [X]": the main session marks a task [X] only after its own runs show the whole suite passing and no static-check finding the baseline lacked. |
| B | R34 | It marks a task [X] only after its reading of the commits made since the recorded HEAD finds nothing the phase's tasks do not call for. |
| B | R35 | It marks a task [X] only after `git status --porcelain --untracked-files=all`, run before its own suite and static-check runs, lists nothing outside the feature directory. |
| B | R36 | What that `git status` lists is the worker's, and goes back to it as a finding. |
| B | R37 | A task the worker found already done is marked on the suite, the static checks and its reading of the commit or file the worker cites. |
| B | R38 | Run what the project names. |
| B | R39 | Say in the completion report what the project does not name. |
| B | R40 | A worker's report never marks a task. |
| B | R41 | A review the phase calls for, and its fixes, resolve first. |
| B | R42 | Then commit `tasks.md` with a message containing `tasks: mark phase <n>` (after any prefix the project's instructions require). |
| B | R43 | Make no such commit when the phase marked nothing new. |
| B | R44 | Only then start the next phase's worker. |
| L | - | **Observation.** |
| B | N1 | Record HEAD before each worker, a fix hand-off's included, not only each phase's first. |
| B | N2 | When a worker returns, run `git rev-list --count <recorded HEAD>..HEAD` and `git log --format='%h %s' <recorded HEAD>..HEAD`: the commits in that range are the worker's work, whatever its report says. |
| B | N3 | A report that lists tasks done while that range is empty, or whose first or last commit is not the range's, fails verification and goes to a worker as any failed verification does. |
| B | N4 | Mark a task the worker found already done only if the commit its report cites passes `git merge-base --is-ancestor <commit> <recorded HEAD>` or the file it cites passes `git ls-files --error-unmatch <file>`. |
| B | N5 | Write the `Carried out in this session:` line from this observation, not from a worker's report: `none` only when every commit of `git rev-list <first recorded HEAD>..HEAD` is in a worker's range, one of the run's `tasks:` commits or a commit of core's extension hooks; otherwise list the tasks the other commits and edits cover. |
| L | - | **Hand-offs.** |
| B | R45 | This narrows core's "Halt execution if any non-parallel task fails": every unfinished task, failed verification or review finding goes to a worker briefed with it, then verification again. |
| B | R46 | The exception: an unfinished task that changes the feature directory, which this session carries out, as **A clean tree outside the feature** says. |
| B | R47 | A review finding passes when a fresh review of it no longer reports it. |
| B | R48 | A phase gets at most two fix hand-offs. |
| B | R49 | Every hand-off after its first counts, whatever items it carries. |
| B | R50 | When verification still fails after them (a fresh review still reporting its finding included), carry out the phase's remaining items in this session as core does. |
| B | R51 | Tasks a worker reports finding join the current phase in `tasks.md`. |
| B | R52 | Commit them with a message containing `tasks: add found tasks`. |
| B | R53 | They go to the phase's next hand-off. |
| B | R54 | Outside the items this session carries out, your only edits to tracked files are `tasks.md` (checkboxes, found tasks) and its commits. |
| B | R55 | Running the suite, the static checks or core's extension hooks is not writing code. |
| L | - | **Reviews.** |
| B | R56 | Start any review the user's or the project's instructions, or a command, call for in a fresh context: `subagent_type: "general-purpose"`, with `model` set to this session's model family (for example `opus`) and no `effort`. |
| B | R57 | Never start a review in a worker. |
| B | R58 | Where no fresh context can be started, the review does not run and the completion report says so. |
| L | - | **Hooks.** |
| B | R59 | A call a project hook blocks is the worker's to follow or report. |
| B | R60 | Never make such a call yourself, in the fallback too. |
| B | R61 | Such a task is not handed off again. |
| B | R62 | It stays unmarked and goes into the completion report. |
| B | R63 | The next phase starts without it. |
| B | R64 | Unless the suite is red because of it, in which case core's "Halt execution if any non-parallel task fails" applies and the run ends with the report. |
| L | - | **Fallback.** |
| B | R65 | When no worker can carry on (no Agent tool, a worker's error, a usage limit included, a missing report, a project that is not a git repository, or uncommitted changes outside the feature directory when the run starts), carry out the remaining tasks in this session as core does. |
| B | R66 | Say which and why in the completion report. |
| B | R67 | The bound of two fix hand-offs is narrower: it moves only that phase's remaining items into this session, and the next phase goes to a worker as usual. |
| B | R68 | The completion report always carries the line `Carried out in this session: none`, or `Carried out in this session:` followed by the task ids and, for fix items, the phase and a short name of each. |
| L | - | **Where a run starts.** |
| B | R69 | `tasks.md`'s marks, `[X]` or `[x]`, read from the file as core reads it, are the record of what is done, whoever made them. |
| B | R70 | Where a run starts is never read from commit messages. |
| B | R71 | A run takes the phases in order and skips every phase whose tasks are all marked, wherever it falls. |
| B | R72 | It starts at the first phase with an unmarked task, at Phase 1 when none is marked. |
| B | R73 | When every task is marked, start no worker, commit nothing. |
| B | R74 | Then say so in the completion report in place of the line below. |
| B | R75 | Each phase's baseline is taken as Verification says. |
| B | R76 | Work committed before the run is covered by the whole-suite run only. |
| B | R77 | When a phase went to a worker, the completion report carries the line `Started at phase <n>: work committed before this run was covered by the whole suite, not read as a diff, its static-check findings in the baseline.` |
| L | - | **A clean tree outside the feature.** |
| B | R78 | Before the first worker and before any of the run's own suite or static-check runs, run `git status --porcelain --untracked-files=all`. |
| B | R79 | When it lists a path outside the feature directory, carry out the run in this session as core does (**Fallback**). |
| B | R80 | In that case, name those paths in the completion report. |
| B | R81 | Inside the feature directory, uncommitted changes stay as they are: the run neither asks about them nor stops for them. |
| B | R82 | They are not a finding. |
| B | R83 | No worker edits, stages, commits or reverts a file there. |
| B | R84 | Commits that core's extension hooks make are core's, not the run's. |
| B | R85 | The run's `tasks: mark phase` and `tasks: add found tasks` commits carry `tasks.md` as it stands, its earlier edits included. |
| B | R86 | A task that changes a file in the feature directory is carried out in this session as core does, all of it. |
| B | R87 | Its files in the feature directory are left uncommitted, as core leaves them. |
| B | R88 | What this session changes outside the feature directory while carrying out items, it commits as soon as it has carried them out, before any later Verification or worker, in a commit whose message contains `tasks: carried out in this session`. |
