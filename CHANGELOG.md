# Changelog

All notable changes to this preset are recorded here, in the form of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) as constitution V defines it.

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

[0.1.0]: https://github.com/camilopiedra92/spec-kit-preset-story-workers/releases/tag/v0.1.0
