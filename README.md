# spec-kit-preset-story-workers

A [Spec Kit](https://github.com/github/spec-kit) preset that would have `/speckit-implement` hand
each phase of a feature's tasks to a worker subagent on a smaller model (Sonnet), while the main
session (Opus) verifies, reviews and decides.

**Status: measured and not adopted.** The eval below showed the preset using more, not less,
usage than core `/speckit-implement` on its fixture, so no release was made (constitution III).
The fragment, the harness and the raw results are in this repository, with no version tag, so
nothing here is installable as a release; the measured state is tagged
[`measured-not-adopted-2026-10-14`](https://github.com/camilopiedra92/spec-kit-preset-story-workers/tree/measured-not-adopted-2026-10-14).

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
fixture the Opus share (main session and reviews) alone cost more than core's whole run. A remeasure needs a
fixture whose phases carry enough work for delegation to pay for its per-phase verification, and
that is a new feature with its own spec.

**Raw outputs.** `tests/eval/results/2026-10-14/` on the tag: each arm's `status`, `usage.txt`,
`heldout.txt`, `suite.txt`, `versions.txt`, `models.txt`, `commits.txt` and `report.txt`, plus
`with/attribution.txt` and `probes.txt`. The stream files are not committed because they carry
local paths and session IDs. The steps to rerun are in `specs/001-story-workers/quickstart.md`.
