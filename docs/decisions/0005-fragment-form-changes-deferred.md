# 0005. Changes to the fragment's form that need an eval are deferred; two that do not are made

- Status: the two changes made stay accepted. The deferral of the other three is **superseded by
  [feature 004](../../specs/004-fragment-form-and-observation/spec.md)** (2026-10-23): items 1 and 2
  are implemented and measured there, item 3 stays moot. The reason given below for deferring was
  wrong (see "Correction"); this record keeps what was decided and when.
- Date: 2026-10-22
- Source: an outside review of the text the Spec Kit presets add (owner-commissioned, 2026-10-22,
  kept outside this repository); each claim below was checked against the fragment, not taken from
  it. Constitution III is the reason for the split.

## Context and problem statement

The review found the fragment's form harder for a model to follow than its substance deserves.
Constitution III asks an eval for a rule added, changed or dropped, and this repository's evals
spend model usage. The session that wrote this record took the owner to have declined that spend;
he had not (see "Correction"). Which of the findings can be applied without an eval?

## Correction, 2026-10-23

This record said the owner "declined to spend [usage] now". That was **the orchestrating session's
misreading, not an owner decision**: the owner's refusal to pay concerned GitHub Actions only, and
model usage from his subscription for evals is approved. The split below (two changes made without
an eval, three deferred) was taken for that reason and is kept as a record of what was decided on
2026-10-22, not as the owner's position. On 2026-10-23 the owner decided not to defer the rewrite
("no diferir la reescritura") and to measure it: feature 004 implements deferred items 1 and 2 and
runs the evals of constitution III for them and for the paragraph made here, whose "behaviour not
measured" is replaced by the measurement once it is recorded in the README. Nothing is released
until the owner decides after reading it.

## Decision outcome

**Made (no rule added, removed or reordered; behaviour not measured):**

- A first paragraph in the fragment saying that in a project that is not a git repository, **The
  call** sends the run to **Fallback**. It restates the two rules as written (The call: "when the
  project is not a git repository ... go to **Fallback**"; Fallback: "carry out the remaining tasks
  in this session as core does, and say which and why in the completion report"); it claims nothing
  about what a model does. `tests/compose.sh` compares the paragraph whole, in the fragment and in
  the composed skill. Seen red before the edit and with the paragraph removed by hand (2026-10-22,
  specify 1.2.2).
- "Narrows" for core's "For completed tasks, make sure to mark the task off as [X]" is kept. The
  review read it as a replacement of the trigger. Here "narrows" is the word for every core rule the
  fragment names and changes (constitution I, README "What it narrows in core", which lists the
  other two rules in the same words), and this one is narrowed in the strict sense too: core marks
  every completed task, the fragment marks the completed tasks the main session has verified, so
  what it marks is a subset of what core marks, and the worker's brief hands the rule to the main
  session ("core's 'mark the task off as [X]' ... is yours"). A task a worker finished and
  verification rejected stays unmarked; no other task is marked that core would leave unmarked.
  Changing the verb would also have changed the vocabulary of three places for no change in what the
  fragment makes a model do.

**Deferred on 2026-10-22 (each changes the prompt, so each needs an eval first); superseded, items 1 and 2 by feature 004:**

1. One rule per bullet in the three long paragraphs (The brief, Hand-offs, A clean tree outside the
   feature), the rationale moving to the README. Not measured whether the compliance gain the
   review expects exists, or whether the rules lose a qualifier on the way.
2. Checking `Carried out in this session:` and the "found already done" tasks against the tree
   (`git log` between HEADs) instead of the worker's report. A design change: the report is the
   only record today. Eval needed to show it catches something a report-only run misses.
3. (Still moot.) A composition test for story-workers with another preset that appends to `speckit-implement`.
   Moot today: the only other such preset, spec-kit-preset-test-first, was archived on 2026-10-08.
   Reopen if a second preset appends to `implement` again.

### Consequences

- The next release (a PATCH under constitution V, the owner's to cut) carries the first paragraph;
  until then it is under `[Unreleased]` in the CHANGELOG.
- Items 1 and 2 were taken as hypotheses and are feature 004's two stories; their evals are in the
  README.
