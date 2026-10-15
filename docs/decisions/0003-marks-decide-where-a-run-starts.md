# 0003. `tasks.md`'s marks decide where a run starts; nothing is read from history

- Status: accepted
- Date: 2026-10-14
- Source: [research.md R1](../../specs/003-resume-from-head/research.md#r1-what-a-resumed-run-trusts),
  measured in [Eval 003](../../README.md#eval-003-2026-10-14)

## Context and problem statement

A run of `/speckit-implement` can start on a feature that is partly done: interrupted earlier, or
built with core before the preset was installed. Where does it start, and what does it trust about
the work already there? `v0.1.0` resumed after its own last `tasks: mark phase` commit, so a feature
adopted partway through restarted at Phase 1.

## Considered options

1. **`tasks.md`'s marks, `[X]` or `[x]`, read as core reads them**: the first phase with an unmarked
   task; every all-marked phase skipped; each phase verified from HEAD before its first worker.
2. **The phase after the last `tasks: mark phase` commit** (`v0.1.0`).
3. **A baseline reconstructed from history**: the last commit that changed `tasks.md`, or the last
   marker commit, else HEAD (closed PR #4).
4. **Marks as committed at HEAD only.**

## Decision outcome

Option 1. The marks are core's own record of what is done ("For completed tasks, make sure to mark
the task off as [X]"), whoever made them. Every run is treated alike: the brief says an unmarked
task may already be done, the worker checks the code and `git log`, and, when a phase went to a worker, the completion report names
the phase the run started at. Options 2 and 3 read a history with several writers (the preset,
core, hooks, the user) and each was misread in review (PR #4: a baseline after the commits to
verify, a hook-blocked task reopening a finished phase). Option 4 restarts an adopted feature whose
marks were never committed.

### Consequences

- A run is level-triggered: interrupted anywhere, the next run recomputes where it is.
- Work committed before the run is covered by the whole suite only, not re-read as a diff; the
  report says so. Eval 003 showed the cost: `v0.1.0`'s re-verification of a finished phase found a
  gap (`Cart.add`) that `0.2.0` does not look for. Re-verifying finished phases is a separate
  decision (resync), not a reason to read history again.
- A task a hook blocks stays unmarked, so each later run starts at its phase.
