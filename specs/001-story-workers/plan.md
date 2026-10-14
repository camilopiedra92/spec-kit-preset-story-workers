# Implementation Plan: Story workers

**Branch**: `001-story-workers` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-story-workers/spec.md`

## Summary

A preset with one fragment appended to core `speckit-implement`: each phase of `tasks.md` goes to a
worker subagent started with `model: "sonnet"` and `effort: "medium"`, the main session verifies in its own runs before
marking `[X]`, every fix goes back to a worker, and any review is started naming the main session's
model. Nothing is installed in a project. The release is gated on an eval: a committed fixture
implemented without the preset, with it, and with it but no Agent tool, run hermetically and
compared on total usage and on held-out acceptance tests.

## Technical Context

**Language/Version**: Markdown (the fragment); bash (`tests/compose.sh`, `tests/eval/run.sh`,
`tests/check.sh`); Python 3.11+ for `tests/eval/attribution.py`.

**Primary Dependencies**: Spec Kit CLI (`SPECKIT_PINNED` v1.1.0 in CI, as the sibling presets; 1.1.3
locally); Claude Code 2.1.296 for the observations and the eval; `jq`; dev only: ruff, mypy, pytest,
pytest-timeout through uv.

**Storage**: N/A.

**Testing**: `tests/check.sh`, the one command CI runs: ruff (lint and format), mypy, pytest for
`attribution.py`, then `tests/compose.sh`. The eval runs by hand: it calls a model and spends usage.

**Target Platform**: projects using Spec Kit with Claude Code; other agents fall back to core.

**Project Type**: Spec Kit preset.

**Performance Goals**: SC-001, total usage at least 30% lower on the fixture.

**Constraints**: nothing installed in a project; no change to core; the fixture, the held-out tests
and every development file stay out of the archive.

**Scale/Scope**: one fragment (~50 lines), a composition test, an eval harness with a fixture of two
stories, one small Python module with its tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Append, never replace | One fragment, `strategy: "append"`, no frontmatter; it names the two core rules it narrows and `tests/compose.sh` greps core for them. |
| II. Verified against the real CLI | `tests/compose.sh` installs a tag-shaped archive with the real CLI; CI runs `tests/check.sh` pinned on every push and pull request and against the latest release weekly. |
| III. Behaviour is measured, not asserted | The eval (R6) runs the fixture hermetically without the preset, with it and in fallback; the README records the date, usage, held-out results, runs per arm and every tool's and model's version. The preset is released only if SC-001, SC-002 and SC-005 hold. |
| IV. Degrades to core | FR-007 states the fallback beside the hand-off, and the eval's `fallback` arm (no Agent tool) measures it (SC-005), as IV asks where the capability can be withheld. |
| V. Released by tag | `preset.yml`, CHANGELOG and tag move together at release; `tests/compose.sh` fails if the archive carries `.specify/`, `.claude/`, `specs/`, `tests/`, `docs/`, `.github/`, `CLAUDE.md`, `pyproject.toml` or `uv.lock`. |

Re-checked after Phase 1: no violation; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-story-workers/
├── spec.md
├── plan.md
├── research.md          # R1–R6
├── quickstart.md        # running the eval
├── contracts/
│   └── fragment.md      # what the fragment must say, and the harness's interface
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
└── eval/
    ├── run.sh                   # one arm, headless, outputs into <out-dir>
    ├── attribution.py           # SC-003 from stream.jsonl
    ├── test_attribution.py
    ├── fixture/                 # two-story Python feature: spec, plan, tasks, no code
    └── heldout/                 # acceptance tests, copied in only after a run ends
.github/workflows/ci.yml         # job `compose`, matrix pinned/latest, runs tests/check.sh;
                                 # `compose (pinned)` is the required check (constitution)
pyproject.toml, uv.lock          # dev tooling only (export-ignore)
README.md, CHANGELOG.md
```

**Structure Decision**: mirrors `spec-kit-preset-constitution-authoring` (fragment, `tests/compose.sh`,
CI pinned and latest), with the eval beside the composition test under `tests/`. The Python module
gets the repository's linter, formatter, type checker and tests at scaffold, as a new project does.

## Phases after this plan

1. **Scaffold**: `pyproject.toml` with the dev tools, `tests/check.sh`, CI, `.gitattributes` for the
   new development files; then the dotfiles ruleset for the required check, in dotfiles' own PR.
2. **Story 1**: the composition checks first, seen red (no fragment yet; and each narrowed-rule check
   against a core copy with that rule removed), then the fragment and `preset.yml` turn them green.
3. **Story 2**: `attribution.py` test-first; the fixture, the held-out tests and `run.sh` (its
   refusals and counting rules driven against stub `claude` streams first); one run per arm; the README entry. On a fail of SC-001 or SC-002, the README entry alone goes to `main` and
   the branch is tagged (Clarifications).
4. **Before the PR**: research R7 moves to `docs/decisions/0001-worker-effort.md` (MADR), and the
   project CLAUDE.md points at `docs/decisions/`.
5. **Release** (on a pass): `preset.yml` version 1.0.0, CHANGELOG, tag `v1.0.0`; then dotfiles'
   `sdd-init` installs it, as its own change with its check.

## Complexity Tracking

None.
