# 0004. Workers need a clean tree outside the feature directory, else the run is core's

- Status: accepted
- Date: 2026-10-14
- Source: [research.md R4](../../specs/003-resume-from-head/research.md#r4-uncommitted-work-a-clean-tree-outside-the-feature-directory),
  measured in [Eval 003](../../README.md#eval-003-2026-10-14) (`phase-2-done-doc-task`,
  `phase-2-done-dirty`)

## Context and problem statement

The main session verifies a worker by reading what changed after it. Changes the user left
uncommitted before the run must stay the user's: never a finding, never committed or reverted by
the run. How does the run keep the user's changes apart from a worker's?

## Considered options

1. **A clean tree outside the feature directory**: `git status --porcelain --untracked-files=all`
   before the first worker; a path outside the feature directory sends the whole run to core. Inside
   it, uncommitted changes stay as they are and no worker writes there.
2. **A record of `git status` taken at the start**, workers never touching a listed file.
3. **Falling back to core on any uncommitted change.**
4. **Handing uncommitted changes to a worker to finish or discard** (`v0.1.0`).

## Decision outcome

Option 1, chosen by the owner after the third fresh review. With nothing uncommitted outside the
feature directory, every change there after a worker is that worker's, so no record is needed and
none can be misread. Option 2 failed review twice: a worker's edit to an already changed file
leaves its status line as it was, untracked directories collapse to one line, and the main
session's own uncommitted work reads as a worker's. Option 3 would rarely let the preset run, since
spec files are usually uncommitted at implement time. Option 4 commits or discards the user's work.

### Consequences

- Workers never write the feature directory; a task that does is carried out by the main session,
  left uncommitted. The main session commits what it carries out outside it
  (`tasks: carried out in this session`) before any later Verification.
- A project with uncommitted work outside the feature directory runs as core until it is committed:
  the preset's own install and updates (the README says to commit them), generated files git does
  not ignore, a monorepo's sibling project.
- Each git worktree is checked on its own: features in parallel worktrees do not affect each other.
