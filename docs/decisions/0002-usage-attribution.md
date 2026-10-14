# 0002. A run's usage is read from its session transcripts, reconciled on every run

- Status: accepted
- Date: 2026-10-14
- Source: [research.md R1–R4](../../specs/002-large-phase-remeasure/research.md#r3-usage-attribution-transcripts-reconciled)

## Context and problem statement

An eval of this preset compares usage between arms, and explaining a result needs to know where the
usage went: the main session against its subagents, and the main session phase by phase. Claude
Code reports a headless run's usage per model only (`modelUsage`). Where can usage per turn be
read, and how can an eval rely on it?

## Considered options

1. **The session transcripts** Claude Code writes under `~/.claude/projects/` (the main session and
   each subagent), reconciled with `modelUsage` and `costUSD` on every run.
2. **The `stream-json` events** of the run.
3. **`modelUsage` alone.**
4. **The subagents' `task_notification` usage.**

## Decision outcome

Option 1. Observed on 2026-10-14 on 001's three runs (Claude Code 2.1.299): the transcripts'
assistant entries, deduplicated by message id, add up exactly to `modelUsage` per model and token
type, and at the list prices to `costUSD` to the last digit; the stream misses some subagent turns
and reports output tokens before they are final; `modelUsage` has no per-turn split;
`task_notification` gives one total per subagent. The transcript format is internal to Claude
Code, so `tests/eval/usage.py` reconciles it on every run, and a run that does not reconcile is not
counted rather than attributed by guess.

### Consequences

- Every eval run's usage is attributed by part (main session, its phases, workers, reviews, other
  subagents) or the run is rerun; a Claude Code release that changes the format shows as
  unreconciled runs, not as a wrong split.
- The price table in `usage.py` carries its source and date; a price change shows the same way.
- Transcripts carry local paths and session ids, so they are copied into a run's directory and
  never committed; `usage.json` carries both sides of the reconciliation so committed results can
  be re-judged.
