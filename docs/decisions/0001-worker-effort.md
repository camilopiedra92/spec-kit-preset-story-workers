# 0001. The worker's effort is set on its call

- Status: accepted; in effect since the preset's release as v0.1.0 on the owner's acceptance
  (README, "The owner's decision, 2026-10-14"), after Eval 001 (not adopted, +65% usage) and
  Eval 002 (no quality difference measurable)
- Date: 2026-10-13
- Source: [research.md R7](../../specs/001-story-workers/research.md#r7-the-workers-effort-is-set-this-is-an-exception)

## Context and problem statement

The fragment starts each worker with the Agent tool. Without an `effort` on the call, a subagent
inherits the main session's effort (research.md R1 5, observed on Claude Code 2.1.296: Sonnet's
thinking tokens on the same problem were 174 with the session at `low` and 516 at `max`). The
owner's policy (dotfiles `docs/claude-settings.md`) leaves effort at each model's default, because a
written level freezes and nobody revisits it.

Should the worker's call set its effort?

## Considered options

1. **`effort: "medium"` on the worker's call; nothing on the review's.**
2. **Inherited**: no `effort` on the call.
3. **`effort: "low"`** on the worker's call.

## Decision outcome

Option 1. Raising the session's effort to plan a hard feature would otherwise raise every
worker's, which is the opposite of the feature's aim of moving the bulk of the work off the larger
model's budget. Medium is Opus's default today (dotfiles `docs/claude-settings.md`, citing the
model-config docs), so at default settings the eval measures what an unset value would. A review
inherits: it should think as hard as the session the owner chose.

### Consequences

- On a release, the one exception to the owner's policy: dotfiles' `docs/claude-settings.md` is to
  name it and link here (done in dotfiles PR #149, 2026-10-14).
- The revisit the policy asks for is built in: the eval reruns whenever a rule changes
  (constitution III) and records each model's effort in `versions.txt`, and the probes check that
  the call's effort still applies (R1 5 and 8; both held on Claude Code 2.1.299).
- A later feature that wants another level for the worker reopens this record with an eval, not
  by editing the fragment.

### Why the others lost

- **Inherited**: no written level, but it couples the worker's effort to the session's, above.
- **`low`**: cheaper, and unmeasured on a phase's work; the eval measures `medium`.
