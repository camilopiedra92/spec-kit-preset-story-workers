# Implementation Plan: Story workers

**Branch**: `001-story-workers` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-story-workers/spec.md`

## Summary

A preset with one fragment appended to core `speckit-implement`: each phase of `tasks.md` goes to a
worker subagent started in the foreground with `model: "sonnet"` and `effort: "medium"`; the main session verifies in
its own runs and reads the diff before marking `[X]`, sends every fix back to a worker, starts any
review naming its own model family, and falls back to core whenever a worker cannot carry on.
Nothing is installed in a project. The release is gated on an eval run hermetically — a committed
fixture implemented without the preset, with it, and with it but no Agent tool — compared on total
usage and on held-out acceptance tests, and on probes that rerun the observations the design rests
on. On a pass, the owner's setup adopts it (dotfiles, existing projects).

## Technical Context

**Language/Version**: Markdown (the fragment); bash (`tests/check.sh`, `tests/compose.sh`,
`tests/eval/run.sh`, `tests/eval/probes.sh`); Python 3.11+ for `tests/eval/attribution.py` and `tests/eval/bounded.py`.

**Primary Dependencies**: Spec Kit CLI (`SPECKIT_PINNED` v1.1.0 in CI, as the sibling presets; 1.1.3
locally); Claude Code 2.1.296–2.1.299 for the observations (R1 names each one's), and whatever the eval runs on, recorded in its `versions.txt`; `jq`; dev only: ruff, mypy, pytest,
pytest-timeout through uv.

**Storage**: N/A.

**Testing**: `tests/check.sh`, the one command CI runs: ruff (lint and format), mypy, pytest (for
`attribution.py`, `bounded.py`, and `run.sh`'s refusals and counting driven against stub `claude`
streams), then
`tests/compose.sh`. The Python steps join it with the first Python file (Story 2): before that there
is nothing for mypy or pytest to check, and both exit non-zero on an empty tree (mypy 2, pytest 5,
observed 2026-10-13). The eval and the probes run by hand: they call a model and spend usage.

**Target Platform**: projects using Spec Kit with Claude Code; other agents fall back to core.

**Project Type**: Spec Kit preset.

**Performance Goals**: SC-001, total usage at least 30% lower on the fixture.

**Constraints**: nothing installed in a project; no change to core; every development file stays out
of the archive.

**Scale/Scope**: one fragment (~60 lines), a composition test, an eval harness with a two-story
fixture, twelve probe runs over eleven observations, two small Python modules with their tests; the ruleset in dotfiles at scaffold, three more
dotfiles changes and one commit per approved project at rollout.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Append, never replace | One fragment, `strategy: "append"`, no frontmatter; it names the three core rules it narrows, and `tests/compose.sh` runs `tests/core-anchors.sh` on core for them and for each step the brief names. |
| II. Verified against the real CLI | `tests/compose.sh` installs a tag-shaped archive with the real CLI; CI runs `tests/check.sh` pinned on every push and pull request and against the latest release weekly. |
| III. Behaviour is measured, not asserted | The eval (R6) runs the fixture hermetically in three arms and the probes rerun R1; the README records the date, usage, held-out results, runs and reruns, probes, and every tool's and model's version and effort. Released only if every success criterion holds. |
| IV. Degrades to core | FR-007: no Agent tool, a worker's error or usage limit, or the hand-off bound, and the session carries on as core does; the `fallback` arm measures it (SC-005). |
| V. Released by tag | `preset.yml`, CHANGELOG and tag move together at release; `tests/compose.sh` fails if the archive carries `.specify/`, `.claude/`, `specs/`, `tests/`, `docs/`, `.github/`, `CLAUDE.md`, `.gitignore`, `pyproject.toml` or `uv.lock`. |

Re-checked after Phase 1: no violation; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-story-workers/
├── spec.md
├── plan.md
├── research.md          # R1 observations (16 items), R2–R7 decisions and alternatives
├── quickstart.md        # running the probes and the eval
├── contracts/
│   └── fragment.md      # the fragment's rules, the harness's and the probes' interface
├── checklists/
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
preset.yml                       # id story-workers; one command template, append
commands/
└── speckit.implement.md         # the fragment
tests/
├── check.sh                     # the one command: ruff, mypy, pytest, compose.sh
├── compose.sh                   # archive → real CLI → composed skill checks
├── core-anchors.sh              # <skill-file>: core still carries each narrowed rule and step
└── eval/
    ├── run.sh                   # one arm, hermetic, outputs into <out-dir>
    ├── probes.sh                # reruns research R1's observations
    ├── bounded.py               # runs a command in its own process group under a deadline
    ├── attribution.py           # SC-003 from stream.jsonl
    ├── test_attribution.py
    ├── test_run.py              # run.sh's refusals and counting, against stub claude streams
    ├── test_bounded.py          # the deadline kills the whole group
    ├── fixture/                 # two-story Python feature: spec, plan, tasks, uv.lock, and a
    │                            # CLAUDE.md with the commit rule and a review per story
    ├── heldout/                 # acceptance tests, copied in only after a run ends
    └── reference/               # a correct implementation of the fixture, proving the oracle
.github/workflows/ci.yml         # job `compose`, matrix pinned/latest, runs tests/check.sh;
                                 # `compose (pinned)` is the required check (constitution)
docs/decisions/0001-worker-effort.md   # MADR, from research R7, before the PR opens
pyproject.toml, uv.lock          # dev tooling only (export-ignore)
.gitignore                       # virtualenv and tool caches (export-ignore)
README.md, CHANGELOG.md
```

In dotfiles, at rollout: `bin/sdd-init.sh` and `checks/90-spec-kit.sh` (the second preset URL and its
check), `docs/claude-settings.md` (the effort exception), and `github/repos.json` (this repository's
ruleset, at scaffold, as soon as CI exists).

**Structure Decision**: mirrors `spec-kit-preset-constitution-authoring` (fragment, `tests/compose.sh`,
CI pinned and latest), with the eval and probes beside it under `tests/`. The Python modules get the
linter, formatter, type checker and tests with the first of them (Story 2), scoped to the harness's
own modules and tests: the fixture, held-out tests and reference implementation are checked by the
runs that use them.

## Phases after this plan

1. **Scaffold**: `.gitignore`, `tests/check.sh` (running `tests/compose.sh`), CI, `.gitattributes`
   for the new development files. Then, in dotfiles' own PR, this repository's ruleset in
   `github/repos.json`.
2. **Story 1**: the composition checks first, seen red (no fragment yet; and each narrowed-rule and
   step check against a core copy with that phrase removed), then the fragment and `preset.yml` turn
   them green.
3. **Story 2**: the Python toolchain (`pyproject.toml` with the dev tools, `uv.lock`, and its steps in
   `tests/check.sh`) with the first Python files; `attribution.py` and `run.sh`'s counting test-first against stub streams; the
   fixture, the held-out tests, `run.sh` and `probes.sh`; the probes, then one counted run per arm;
   the README entry. If any success criterion does not hold, the branch merges with the README
   recording it as not adopted, with no release (Clarifications).
4. **Before the PR**: research R7 moves to `docs/decisions/0001-worker-effort.md` (MADR), and the
   project CLAUDE.md points at `docs/decisions/`.
5. **Release** (on a pass): `preset.yml` version 1.0.0, CHANGELOG, tag `v1.0.0`.
6. **Story 3** (rollout): a dotfiles PR — `sdd-init` installs the tag beside `constitution-authoring`,
   `checks/90-spec-kit.sh` seen red without it, `docs/claude-settings.md` names the exception — and,
   for each existing Spec Kit project the owner approves (`renta`, `RENPHO`, `supertrader`,
   `dotfiles`), `specify preset add` of the tag in a commit of its own. The global `CLAUDE.md` is left
   as it is: its "each story closes with the whole suite, the project's mutation check … and a fresh
   review" is a review the user's instructions call for, which FR-005 starts on the main session's
   model, a phase's rules belong in a preset, and it is at 199 of
   200 lines.

## Complexity Tracking

None.
