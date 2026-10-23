# Research: Fragment form, and observed verification

Decisions and the alternatives each beat. Dated 2026-10-23. Claims about model behaviour here are
reasoning, not measurement, until the README's E1 to E3 say otherwise.

## R1. Restructure the whole fragment, not three paragraphs

- **Chosen**: every section into one rule per bullet (88 inventoried rules), labels kept as the
  sections' names.
- Considered: only The brief, Hand-offs and A clean tree (the review's three). Lost: Verification,
  Where a run starts and Fallback are as dense, and a fragment half in bullets and half in paragraphs
  is read two ways.
- Considered: shorten the rationale and keep the paragraphs. Lost: the review's complaint is a rule
  and its exceptions chained in one sentence, which cutting the rationale does not change.

## R2. How "no rule changed" is made checkable

- **Chosen**: an inventory of the old text (spec), a mapping of each rule to one new block (plan), a
  test comparing the mapping to the composed skill, and a fresh-context reviewer comparing old and
  new text for equivalence of meaning. The first three catch a lost, doubled or extra block; only
  the reviewer can say a block still means what the old clause did. The spec states that this last
  step is not automated.
- Considered: a stable marker (`<!-- R12 -->`) in each shipped bullet for the test to grep. Lost: it
  puts bookkeeping into a prompt whose complaint is attention spent on text that is not a rule, and
  the mapping table carries the same information outside it.
- Considered: only grep phrases (what `compose.sh` already does). Lost: a phrase proves a clause
  exists, not that no rule was dropped beside it or split wrongly.

## R3. Splitting a sentence into rules: where the line is

A rule is one thing to do, not do, or know. A sentence with a list of independent items (the
report's six fields, the brief's carried items) is one bullet per item. A sentence with conjunctive
conditions on one act (marking a task [X]) is one bullet per condition, each stating the act, so a
missed condition can be seen. A parenthesis that qualifies a rule (the prefix a project requires)
stays inside it; a parenthesis that is a rule of its own (the feature-directory exception) is its
own bullet. The cost is repetition ("It marks a task [X] only after" three times); it was accepted
for the sake of one rule per bullet.

## R4. Observation: what the main session can run

- **Chosen**: `git rev-list` and `git log` over the range from the HEAD recorded before the worker;
  `git merge-base --is-ancestor` and `git ls-files --error-unmatch` for what a report cites. All are
  read-only, already within "running the suite, the static checks ... is not writing code".
- Considered: a ledger and an audit replayed from tool calls, as the archived test-first preset did.
  Lost: it needs hooks and a runner the preset cannot install (principle I, append only) and is a
  different design, not a smaller one.
- Considered: asking the worker to put a trailer in its commits. Lost: still the worker's word.
- Considered: comparing the worktree's file hashes. Lost: more rules, and the suite and the commit
  range already bound what changed.
- The foreground worker (`run_in_background: false`) is what makes the interval attributable: nothing
  else commits between the main session's record and the worker's return, short of the user.

## R5. Evaluation design

- **Chosen**: the repo's harness, arms differing only in `--preset <ref>`; `phase-2-done-doc-task`
  for E1 and E2 because a worker runs, a task is carried out in-session and the resume path is
  exercised, so most of the rules the rewrite touches are in play; `checkout` fresh, `--no-git`, for
  E3. Three counted runs per arm.
- Considered: `runs.sh`. Lost: its gate is Eval 002's (a `without` miss opens the `with` runs); here
  every arm is `with`.
- Considered: a fresh `checkout` for E1 and E2 too. Lost for cost; `fresh` runs the same rules
  without the resume and the in-session path.
- Considered: building a worker that misreports, to test N3 to N5 directly. Lost for now: a staged
  lie measures the staged lie. Left as the open question the results name.
- Pass conditions are not gates (spec): a worse result is recorded as it is.

## R6. The deferral's reason

0005 recorded "the owner declined to spend now" as the reason to defer. The owner's refusal
concerned GitHub Actions; the orchestrating session misread it. 0005 now says so and is superseded
by this feature; the same sentence is corrected in the CHANGELOG. Nothing else in the repository
repeated it (grep, 2026-10-23).
