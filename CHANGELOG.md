# Changelog

All notable changes to this preset are recorded here, in the form of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) as constitution V defines it.

## [0.1.1] - 2026-10-14

### Fixed

- Resume no longer restarts a feature adopted partway through at Phase 1. Where a run resumes is now
  read from `tasks.md`'s marks as committed, core's own record of what is done (core
  `speckit-implement`: "For completed tasks, make sure to mark the task off as [X]" and "All tasks
  in tasks.md completed and marked `[X]`"), instead of from this preset's `tasks: mark phase <n>`
  commits. The rest of the rule is this preset's own: the baseline at the last `tasks: mark phase`
  commit (or HEAD), the worker briefed with the phase's commits and only its unmarked tasks, a
  resumed phase's own two fix hand-offs, a phase with uncommitted marks verified rather than
  skipped, and the user asked before uncommitted work is committed or handed off. Neither this rule
  nor the one it replaces was measured (no eval runs a resumed feature); released on the owner's
  acceptance: see [the owner's decision](README.md#the-owners-decision-2026-10-14).

## [0.1.0] - 2026-10-14

Released on the owner's acceptance, without an eval showing the claimed effect (constitution III,
v2.0.0): see [the owner's decision](README.md#the-owners-decision-2026-10-14). Eval 001 measured
65% more usage than core on a small fixture; Eval 002 could not measure a quality difference.

### Added

- `## Story workers`, appended to core `speckit-implement`: each phase of `tasks.md` goes to one
  foreground worker on `sonnet` at `effort: "medium"`; tasks are marked `[X]` only after the main
  session's own suite, static checks and diff reading; fixes go back to a worker, at most two per
  phase; reviews run on the main session's model family; without the Agent tool, a worker, or git,
  the session carries on as core does and says so in its report.

[0.1.1]: https://github.com/camilopiedra92/spec-kit-preset-story-workers/releases/tag/v0.1.1
[0.1.0]: https://github.com/camilopiedra92/spec-kit-preset-story-workers/releases/tag/v0.1.0
