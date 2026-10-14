# spec-kit-preset-story-workers

A [Spec Kit](https://github.com/github/spec-kit) preset that has `/speckit-implement` hand each
phase of a feature's tasks to a worker subagent on a smaller model (Sonnet), while the main session
(Opus) verifies, reviews and decides.

**Status: released as `v0.1.0` on the owner's decision, without an eval showing its claimed
effect.** Two evals, below, are recorded as they came out: [Eval 001](#eval-2026-10-14) measured the
preset at **65% more usage** than core on a small fixture, and [Eval 002](#eval-002-2026-10-14)
could not measure a quality difference, core passing every held-out test in six runs on two
versions of a larger fixture, so the cost question on large phases was not run. The owner accepted
the preset on 2026-10-14 under constitution III (v2.0.0): [the decision](#the-owners-decision-2026-10-14).
The measured state of 001 is tagged
[`measured-not-adopted-2026-10-14`](https://github.com/camilopiedra92/spec-kit-preset-story-workers/tree/measured-not-adopted-2026-10-14).

## Install

```bash
specify preset add --from https://github.com/camilopiedra92/spec-kit-preset-story-workers/archive/refs/tags/v0.1.0.zip
```

It appends a `## Story workers` section to core `speckit-implement` and replaces nothing
(constitution I). Each phase of `tasks.md` goes to one foreground worker started with
`model: "sonnet"` and `effort: "medium"`; the main session marks a task `[X]` only after its own
run of the suite, the static checks and a reading of the phase's diff; fixes go back to a worker
(at most two per phase); any review runs on the main session's model; and with no Agent tool, a
worker error or no git, the session carries on as core does and says so in its report. To update,
add the newer tag's archive the same way.

**What it narrows in core**, by name: "For completed tasks, make sure to mark the task off as [X]"
(the main session marks, after verifying), "parallel tasks [P] can run together" (one worker per
phase, `[P]` tasks run in turn inside it) and "Halt execution if any non-parallel task fails" (a
blocked task stays unmarked and the run goes on unless the suite is red).

**When not to use it.** When usage is what you are optimising: the only measurement says it costs
more (Eval 001). When the main session already runs on the smaller model. With agents that have no
subagents (it falls back to core, so it only adds text).

## The owner's decision, 2026-10-14

After Eval 002's second closed gate, the owner chose to stop measuring and release the preset as it
was measured, unchanged since Eval 001 (fragment at commit `894aecf`). The constitution was amended
for it (v2.0.0, principle III: a rule whose eval does not show its claimed effect may be released
when the owner accepts it, with the result recorded as it is). Recorded as it stands: no eval has
shown the preset to save usage, and one measured it costing 65% more; no eval could show a quality
difference either way. Accepted as released, not as measured to work.

## Eval 002, 2026-10-14

**What was planned.** The same fragment, unchanged (FR-006; checked at each attempt with
`git diff 894aecf -- commands/ preset.yml`), on a fixture whose phases are large, in three arms of
three counted runs each, judged on medians, with every run's usage reconciled with `costUSD` from
the session transcripts and split by phase. The `without` runs came first and gated the rest: `with`
and `fallback` run only once a `without` run misses a held-out test, so the eval could show a
quality difference (spec FR-003). Spec, plan and reviews: `specs/002-large-phase-remeasure/`.

**Fixture.** `tests/eval/fixtures/checkout/`, a cart-pricing feature in a uv Python project: a setup
phase and three story phases (catalog, cart and tax; promotions with stacking, a cap and
exclusivity; returns with per-unit allocation), held-out tests proven by a reference
implementation (`tests/eval/oracle.sh`) and reviewed in a fresh context
(`specs/002-large-phase-remeasure/heldout-review.md`). One synthetic feature, however large, is less
representative than a real one.

**Gate history.** Both attempts' outputs are under
`tests/eval/results/002-large-phase-remeasure/attempt-<k>/` (no streams or transcripts: they carry
local paths and session ids).

| Attempt | Fixture (commit) | Task lines per story phase | Held-out N | `without` runs | Gate |
|---|---|---|---|---|---|
| 1 | `538f5cd` | 9, 8, 6 | 46 | 46/46 · 46/46 · 46/46 | closed |
| 2 | `ee08036`, hardened | 10, 10, 9 | 59 | 59/59 · 59/59 · 59/59 | closed |

The hardening (commit `866a3bc`) added five stated rule groups, each aimed at a reading that is easy
to compute at the wrong step: a bulk price from 10 units rounded per unit; free units valued at it;
a minimum net checked on the current net; free units outside the cap; a restocking fee rounded once
and capped per order. Each rule's wrong reading, applied to the reference, turned its held-out tests
red. Core still passed them all.

**Runs.** Three counted `without` runs per attempt; every try counted at once, no rerun; no
deadline change. `with` and `fallback` never ran, so no success criterion of the comparison
(SC-001, SC-002, SC-003, SC-005, SC-007) was judged.

| Run | Held-out | Suite | Total | Main session | Reviews (3) |
|---|---|---|---|---|---|
| attempt 1, `without-1` | 46/46 | green | $1.789 | $1.217 | $0.571 |
| attempt 1, `without-2` | 46/46 | green | $1.960 | $1.262 | $0.698 |
| attempt 1, `without-3` | 46/46 | green | $1.827 | $1.147 | $0.679 |
| attempt 2, `without-1` | 59/59 | green | $1.860 | $1.254 | $0.606 |
| attempt 2, `without-2` | 59/59 | green | $1.779 | $1.171 | $0.607 |
| attempt 2, `without-3` | 59/59 | green | $1.951 | $1.274 | $0.677 |

Medians: attempt 1 $1.827 (min $1.789, max $1.960); attempt 2 $1.860 (min $1.779, max $1.951).
Three runs bound what can be said about variance to these extremes. Every run's usage reconciled
with what Claude Code reported, to the token and within $0.000001 (SC-008, `usage.txt` per run).
Total spent on the eval, probes included: $13.79.

**Checks that did run.** Probes: 14 of 14 ok on Claude Code 2.1.299 in both attempts (SC-006).
SC-004 (the composition test red on each removed core anchor): `tests/compose.sh` on every push,
"8 anchors each turned the check red".

**Isolation and versions.** As Eval 001, plus Claude Code's auto-updater disabled for every run
and the probes. Spec Kit 1.1.3; Claude Code 2.1.299; main session `claude-opus-5-5` at `--effort
medium`; git 2.56.0; uv 0.13.0; Python 3.12.12; pytest 9.1.1; ruff 0.17.0 (each run's
`versions.txt`). Output style `default`, no MCP server, only Claude Code's built-in plugins.

**Reading.** On these fixtures, core `/speckit-implement` on Opus made no mistake a held-out test
could see, in six runs out of six, including on rules built to be misread. So the eval could not
show the preset making code better or worse, and by its own design (the gate) it did not go on to
measure cost on large phases. What remains measured is Eval 001's: on small phases the preset cost
65% more, its main session alone costing more than core's whole session (research R2 of 002).

## Eval, 2026-10-14

**What was compared.** One fixture feature implemented headless by `/speckit-implement` in three
arms: `without` (core only), `with` (the preset) and `fallback` (the preset with the Agent tool
withheld). The arms differ only in the preset and, for `fallback`, the tool.

**Fixture.** `tests/eval/fixture/` on the tag: a uv Python project, one feature (`wordstats`),
two user stories, three phases, five tasks; its `CLAUDE.md` asks for `fixture:` commit messages and
a fresh `general-purpose` review per story. Judged by 12 held-out acceptance tests, at least one
per acceptance scenario, copied in only after each run. One synthetic feature this small is less
representative than a real one.

**Runs.** One counted run per arm, so the result is **directional**. No arm needed a rerun.

**Isolation.** Hermetic: `env -i` keeping only `HOME USER LOGNAME PATH TMPDIR LANG TERM
SPECKIT_PYTHON_EXECUTABLE`; git isolated from user and system config with a fixed `eval`
identity; `--setting-sources project,local --strict-mcp-config`. Every run's `init` event showed
output style `default`, no MCP server, and only Claude Code's built-in plugins.

**Versions.** Spec Kit 1.1.3; Claude Code 2.1.299; main session `claude-opus-5-5` at
`--effort medium`; workers `claude-sonnet-5-5` at `effort: "medium"`; reviews `claude-opus-5-5`,
inheriting the session's effort; git 2.56.0; uv 0.13.0; Python 3.12.12; pytest 9.1.1; ruff 0.17.0.
Harness commit `965d079`; the tag carries a later `run.sh` that differs only in disowning its local
server (two lines, cosmetic, not rerun). `versions.txt` matched across arms but for the date. No
other main-session model or effort was measured.

**Results.** Usage is the per-model `costUSD` Claude Code reports for a headless run, at list
price, subagents included. The subscription window's utilization (`five_hour`, first and last in
the run) is recorded beside it and not used for SC-001, since other sessions move it: `without`
0.08 → 0.09, `with` 0.09 → 0.11, `fallback` 0.11 → 0.11.

| Arm | Opus | Sonnet | Total | vs `without` | Held-out | Own suite | Agent calls | Wall time |
|---|---|---|---|---|---|---|---|---|
| `without` | $0.599 | — | **$0.599** | — | 12/12 | green (12) | 2 reviews | 107 s |
| `with` | $0.753 | $0.232 | **$0.985** | **+65%** | 12/12 | green (14) | 3 workers, 2 reviews | 196 s |
| `fallback` | $0.404 | — | **$0.404** | −33% | 12/12 | green (11) | none | 60 s |

**Success criteria** (spec SC-001 to SC-007):

| | Criterion | Result |
|---|---|---|
| SC-001 | `with` total usage at least 30% below `without` | **Not met**: 65% above |
| SC-002 | `with` held-out ≥ `without`, its suite green | Met: 12/12 vs 12/12, green |
| SC-003 | `attribution.py`: main session writes only `tasks.md`, Sonnet used, one foreground worker per phase in order, `fixture:` code commits, report line `none`, no denials | Met: every clause ok |
| SC-004 | Composition test red when a narrowed rule or step is removed | Met: seen red for each of the 8 core anchors |
| SC-005 | `fallback` held-out ≥ `without`, no Agent call, report lists every task | Met: 12/12, no Agent call, `T001`–`T005` |
| SC-006 | Every probe passes on the eval's Claude Code | Met: 14 of 14 checks on 2.1.299 |
| SC-007 | `with` has a `general-purpose`/`opus` review per story | Met: 2 reviews for 2 stories |

**Reading.** The design delegated what it was meant to: Sonnet wrote every line of code, and
Opus only verified, reviewed and decided. But on a feature this small, the Opus share (main
session and reviews together) cost more than core's whole run did ($0.753 against $0.599). The
likely reason, an inference not measured on its own: each phase adds a brief to write, a report to
read, a suite and static checks to rerun, and a diff to read, and none of that work shrinks with
the size of the phase. The saving the hypothesis counts on, implementation work moving to the
cheaper model, needs phases large enough for it to outweigh that fixed cost; this fixture's phases
were one or two tasks each.

Two other differences between arms, as observed and not attributed further: `without` made no
commit after setup (core does not commit; its report says so), while `with` and `fallback` made
eight each, one per task plus one per phase for `tasks.md`, as the fragment asks; and `fallback`
ran no reviews (no Agent tool; its report says they did not run), where `without` ran two.

**Rules measured.** The whole fragment `commands/speckit.implement.md` at the harness commit,
the worker's brief included. **Not measured**: the fallback for a project that is not a git
repository; its source is core's own `git rev-parse --git-dir` check in "Project Setup
Verification".

**Alternative measured and not adopted.** Hand each phase to a Sonnet worker, with the main
session verifying in its own runs before marking `[X]`. Not adopted because SC-001 failed: on this
fixture the Opus share (main session and reviews) alone cost more than core's whole run. A
remeasure needs a fixture whose phases carry enough work for delegation to pay for its per-phase
verification, and that is a new feature with its own spec.

**Raw outputs.** `tests/eval/results/2026-10-14/` on the tag: each arm's `status`, `usage.txt`,
`heldout.txt`, `suite.txt`, `versions.txt`, `models.txt`, `commits.txt` and `report.txt`, plus
`with/attribution.txt` and `probes.txt`. The stream files are not committed because they carry
local paths and session IDs. The steps to rerun are in `specs/001-story-workers/quickstart.md`.
