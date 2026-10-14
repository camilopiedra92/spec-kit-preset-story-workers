# Story Workers Preset Constitution

## Core Principles

### I. Append, Never Replace

The preset appends fragments to core Spec Kit skills and replaces none of them, so upstream changes
to the rest of each skill keep arriving. A fragment carries no frontmatter, because a description
there replaces the skill's own. A fragment that narrows a core rule names that rule, and the
composition test fails when core no longer carries it.

Rationale: a replaced skill freezes core at the version it was copied from, and a project stops
receiving upstream fixes without anyone noticing; Spec Kit's preset system offers `append` for
this reason. Check: `tests/compose.sh` verifies that each composed skill keeps its core body and
description, ends with its fragment, and that core still carries every rule a fragment narrows.

### II. Verified Against the Real CLI

Every change is verified by installing the preset from a tag-shaped archive with the real `specify`
CLI: against the pinned Spec Kit release on every push and pull request, and against the latest
release weekly. The pinned release moves together with `requires.speckit_version` in `preset.yml`.

Rationale: what a project gets is what the CLI composes, not the fragment files; the weekly run
against the latest release is how an upstream change reaches this repository before it reaches a
project. Check: `.github/workflows/ci.yml` runs `tests/compose.sh` pinned and latest; a reviewer
checks that a change to the pinned release also changes `requires.speckit_version`.

### III. Behaviour Is Measured, Not Asserted

A fragment is a prompt, and a prompt's effect is shown by running it. A rule added, changed or
dropped ships only with an eval: a fixture committed under `tests/`, run headless with the agent it
targets, comparing the preset with and without the rule on what the rule claims to change and on
what it must not make worse. The result is recorded in the README with its date, what was compared,
the number of runs per arm (called directional when it is one), and the version of every tool it
ran on — Spec Kit, Claude Code, the model IDs, git and the test runner. A rule whose eval does not
show its claimed effect, or could not measure it, is released only when the owner accepts it: the
README records the measured result as it is, never restated as a pass, beside the owner's decision,
its reason and its date, and the CHANGELOG entry that releases the rule links that record. Without
that recorded acceptance, the rule is not released, and is recorded as an alternative measured and
not adopted, with the reason. A rule that only restates core or the agent's documented behaviour
needs its source cited instead of an eval.

Rationale: an instruction can read well and change nothing, or cost more than it saves; Anthropic's
prompt-engineering guidance puts success criteria and empirical evaluations before iterating on a
prompt, and the sibling test-first preset was archived on 2026-10-08 after its rules proved costly
in real use without such a measurement up front. The eval stays mandatory and its result stays
visible; whether to ship despite it is the owner's call, made in the open. Amended on 2026-10-14
after two evals of the story-workers fragment: 001 measured it at 65% more usage than core on a
small fixture, and 002 could not measure a quality difference, core passing every held-out test in
six runs on two versions of a large fixture; the owner chose to release it. Check: a reviewer
finds, for each changed rule, the eval under `tests/`, its README entry with versions and runs per
arm, the CHANGELOG entry, and, for a rule released without its eval showing the claimed effect, the
owner's recorded decision linked from that CHANGELOG entry.

### IV. Degrades to Core

Every instruction the preset adds names what the agent does when the capability it relies on is
missing — a tool, a model, a hook, an agent other than the one it targets — and that fallback is
core Spec Kit behaviour, never a refusal and never a state worse than core would leave.

Rationale: projects install the preset on machines, agents and versions this repository never sees;
an instruction with no fallback fails there in a way nobody planned for. Check: a reviewer finds the
fallback beside each instruction that depends on a capability, and the eval of principle III covers
it when the capability can be withheld in the fixture.

### V. Released by Tag

Projects install the preset from a tag's archive, so a release is a tag with a matching version in
`preset.yml`, a CHANGELOG entry in Keep a Changelog form, and semantic versioning: MAJOR when a
project's existing tasks or files stop working as before, MINOR for a rule added, PATCH for a fix.
Whatever is not part of the preset is `export-ignore`.

Rationale: the archive is the artifact; a file in the repository that is not export-ignored lands
in every project that installs it. Check: `tests/compose.sh` builds the archive with `git archive`
as GitHub does and fails if the installed preset carries this repository's `.specify/`, `.claude/`,
`specs/`, `tests/`, `docs/` or `CLAUDE.md`; a reviewer checks that `preset.yml`, the CHANGELOG and the
tag agree.

## Governance

This constitution overrides any other practice in this repository where they conflict.

- Changes reach `main` only through pull requests, merged with `gh pr merge --auto` once the
  required `compose (pinned)` check is green; the ruleset that requires it is declared in
  `camilopiedra92/dotfiles` (`github/repos.json`) and applied by its `bin/repo-rules.sh`.
- The owner (camilopiedra92) reviews every pull request against these principles, including a
  change made outside the Spec Kit commands, before it is marked ready.
- Amendments: the owner proposes or approves a change to this file in a pull request of its own, or
  inside the feature whose decision requires it. The commit message carries the impact report:
  version change, principles changed, what still has to exist for a new principle to be met.
- Versioning of this file: MAJOR for a principle removed or redefined incompatibly, MINOR for a
  principle or section added or materially expanded, PATCH for wording.

**Version**: 2.0.0 | **Ratified**: 2026-10-13 | **Last Amended**: 2026-10-14
