# Changelog

All notable changes to this preset are recorded here, in the form of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) as constitution V defines it.

## [Unreleased]

Nothing here is released: no tag, `preset.yml` is still `0.2.0`, and the owner decides after reading
the measured results (feature 004, [spec](specs/004-fragment-form-and-observation/spec.md)).

### Changed

- `## Story workers` is one rule per bullet, in the same order and sections, with the sentences that
  justify a rule moved to the README ([Why the fragment's rules read as they do](README.md#why-the-fragments-rules-read-as-they-do),
  J1 to J6). No rule is added, removed, reordered or reworded in meaning: the 88 statements of the
  fragment at `53059f8` map one to one onto the new bullets (`tests/fragment_rules.py`, run by
  `tests/compose.sh`, seen red with a bullet removed, duplicated, reworded or added). That the new
  text means what the old did is checked by a fresh-context reviewer, not by a test. **The
  behaviour of the rewritten fragment is NOT measured** until Eval 004 is recorded in the README.
### Added

- A first paragraph in `## Story workers` stating that in a project that is not a git repository,
  **The call** sends the run to **Fallback** (core's behaviour, reported). It restates The call and
  Fallback as written; no rule is added, removed or reordered. When it was merged its behaviour was
  not measured, and the description said the owner had declined to spend on evals: that was the
  orchestrating session's misreading, not an owner decision (his refusal concerned GitHub Actions
  only). Its measurement is feature 004's E3 (README, when recorded). Decision and what was
  deferred, superseded by 004:
  [0005](docs/decisions/0005-fragment-form-changes-deferred.md).

## [0.2.0] - 2026-10-14

Measured against `v0.1.0` in [Eval 003](README.md#eval-003-2026-10-14): on a feature adopted with
Phases 1–2 done, `0.2.0` started at Phase 3 and passed its nine checks, in three states; `v0.1.0`
re-verified the finished Phase 2 (a review, a fix worker, an empty mark commit). On a fresh feature
both passed every held-out test and `0.2.0` every check. One run per arm, directional.

### Changed

- Where a run starts: at the first phase of `tasks.md` with a task not marked `[X]` or `[x]`, the
  marks read as core reads them, every all-marked phase skipped; no longer after the last
  `tasks: mark phase` commit, which restarted a feature adopted partway through at Phase 1. With
  every task marked, no worker starts. The completion report names the phase the run started at.
- Every brief carries only the phase's unmarked tasks and its list of the phases already marked
  (in place of what earlier workers finished), says some may already be done, and asks the worker
  to check each against the code and `git log`; the worker reports tasks found already done, which
  the main session marks on the suite, the static checks and the commit or file cited.
- A run needs nothing uncommitted outside the feature directory: otherwise it is carried out as core
  does, naming those paths. Inside the feature directory uncommitted changes stay as they are; no
  worker writes there, and a task that does is carried out by the main session, left uncommitted.
- Verification reads the phase's commits (in place of the diff from the recorded HEAD) and requires
  nothing uncommitted outside the feature directory; workers stage only their own files, and commit
  Project Setup Verification's changes and ignore-file entries for generated files on their own;
  the main session commits what it carries out outside the feature directory
  (`tasks: carried out in this session`); no `tasks: mark phase` commit when a phase marked nothing
  new.
- Project Setup Verification is Phase 1's worker's only, so a run that starts later skips it (was:
  the first phase's).
- Uncommitted changes to `tasks.md` are carried by the run's `tasks:` commits as they stand (was:
  the user's to keep or drop); commits made by core's extension hooks are core's, not the run's.

### Removed

- Reading the diff of work committed before the run: it is covered by the whole suite only, and the
  report says so (`Started at phase <n>: …`).
- Handing uncommitted changes found at the start to a worker to finish or discard, and the baseline
  taken in a temporary `git worktree` at the last marker commit.

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

[0.2.0]: https://github.com/camilopiedra92/spec-kit-preset-story-workers/releases/tag/v0.2.0
[0.1.0]: https://github.com/camilopiedra92/spec-kit-preset-story-workers/releases/tag/v0.1.0
