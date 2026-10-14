# Research: Large-phase remeasure

Feature 001's research (`specs/001-story-workers/research.md`) still holds for everything this
feature does not change: R1's observations, R2–R5's design of the fragment, R6's eval (arms,
isolation, counting, probes) and R7's worker effort (decision 0001). The entries below are what 002
adds or changes. Each observation names when and how it was made.

## R1. Where a run's usage per message can be read

Observed on 2026-10-14 on the three counted 001 runs (Claude Code 2.1.299), from the files they left:

1. **The `stream.jsonl` events are not enough.** Deduplicated by `message.id`, the `with` run's
   assistant events add up to 497,016 cache-read tokens for the main session and 162,184 for Sonnet,
   against `modelUsage`'s 611,585 (Opus, main and reviews together) and 238,598 (Sonnet): some
   subagent turns are not in the stream at all. And each event's `output_tokens` is the count when
   its first block streamed: the main session's add up to 281 against 7,326 in its transcript.
2. **The session transcripts are.** Claude Code writes the main session to
   `~/.claude/projects/<project-slug>/<session_id>.jsonl` and each subagent to
   `<session_id>/subagents/agent-<id>.jsonl`, with `agent-<id>.meta.json` naming its `agentType`,
   `description`, `model` and the `toolUseId` of the Agent call that started it. Their assistant
   entries, deduplicated by `message.id` (the last entry of each), add up **exactly** to
   `modelUsage`, per model and per token type: `with` Opus 46 / 13,490 / 611,585 / 52,760 (input,
   output, cache read, cache write) and Sonnet 26 / 5,875 / 238,598 / 59,752, as `modelUsage` reports.
   The `session_id` is in the stream's `init` event. The hermetic run keeps `HOME`, so its
   transcripts land in the user's `~/.claude/projects`.
3. **Each entry splits cache writes by duration** (`cache_creation.ephemeral_5m_input_tokens`,
   `ephemeral_1h_input_tokens`); the two are priced differently.
4. **List prices reproduce `costUSD` exactly.** With the prices on Anthropic's pricing page
   (platform.claude.com/docs/en/about-claude/pricing, read 2026-10-14) — Opus 5.5 $4 input, $5 5-minute
   write, $8 1-hour write, $0.20 cache read, $20 output per million tokens; Sonnet 5.5 $2, $2.50, $4,
   $0.10, $10 — the transcripts' tokens give $0.5985348 (`without`), $0.753208 (`with` Opus),
   $0.2320418 (`with` Sonnet) and $0.4040008 (`fallback`), each `costUSD` to the last digit. (The
   bundled claude-api skill's table, cached 2026-10-06, lists Sonnet 5.5's cache read at $0.20; the
   pricing page and the reconciliation both say $0.10.) The Sonnet 1-hour write price is not exercised
   by these runs: no Sonnet entry wrote a 1-hour cache.

The transcript format is Claude Code's internal one, not a published interface, which is why the
harness reconciles it on every run (R3) rather than trusting it.

## R2. 001's cost, attributed after the fact

From the same transcripts, priced as R1 4 (observed 2026-10-14):

| 001 run | Main session | Reviews | Workers | Total |
|---|---|---|---|---|
| `without` | $0.382 (14 turns, 405,708 cache read) | $0.216 (2) | — | $0.599 |
| `with` | $0.505 (15 turns, 497,016 cache read) | $0.248 (2) | $0.233 (3) | $0.985 |

The main session that wrote no code cost **more** than the one that wrote all of it, by $0.123; the
workers then added $0.233. So 001's +65% is not "the main session's verification on top of a smaller
main session": delegation did not shrink the main session at all on that fixture. Its turns cost
about the same in both arms (cache reads per turn ~29k against ~33k), and the per-phase work — brief,
report, diff, suite, marking — replaced the coding turns one for one. What this fixture cannot show is
how both arms grow with the size of a phase: in `without` the main session's coding turns grow with
the work; in `with` its turns per phase should stay near constant while the workers absorb the growth.
That is the hypothesis 002 tests, now with a measured baseline instead of an inference.

## R3. Usage attribution: transcripts, reconciled

- **Decision**: whenever a run's stream names a session, whatever its exit, `run.sh` copies the
  run's transcripts (found by the `init` event's `session_id` under `~/.claude/projects`) into
  `<out-dir>/transcripts/`, and a new
  `tests/eval/usage.py <out-dir>` computes the attribution from them. It first reconciles: per model,
  each token type summed over the transcripts must equal `modelUsage`'s, and the priced sum must equal
  `costUSD` within $0.000001. A run whose transcripts are missing or do not reconcile is **not
  counted** (spec Clarifications), with the mismatch as its reason, and rerun within the bound: the
  attribution is this feature's measurement, so a run without it is not one. Reconciliation runs
  before the suite and held-out tests, so a run that does not count writes no `heldout.txt`, as
  001's counting requires.
- **Parts**: every subagent is attributed by its meta file to `review` (a `general-purpose` call not
  on `sonnet`), `worker` (`model: sonnet`) or `other`; the main session's turns are split by phase
  (R4). Each part carries input, output, cache-read, 5-minute and 1-hour cache-write tokens and cost,
  and the parts sum exactly to the per-model totals.
- **Prices** live in `usage.py` as one table with its source and the date it was read; the
  reconciliation is what keeps the table honest — a price change shows as an unreconciled run, not a
  silently wrong split.
- **Rationale**: the stream is incomplete (R1 1); the transcripts are complete and check out to the
  token (R1 2, 4); reconciling on every run turns an internal format into a checked one.
- **Considered and rejected for unreconciled runs**: *counted but unattributed*: the cost would
  still be measured, but SC-008 would then fail with no rerun path, and one lost file would block a
  release; treating it as a failed measurement keeps the rerun bound as the only budget.
- **Alternatives considered**: *the stream's per-message usage*: incomplete (R1 1). *Only
  `modelUsage`*: per model, never per phase, which is what 001 lacked. *`task_notification`'s
  `usage.total_tokens`*: one number per subagent, no token types, nothing for the main session.
  *`CLAUDE_CONFIG_DIR` pointing at a scratch directory, so transcripts stay out of the user's
  `~/.claude`*: the OAuth login lives in the user's config, and R1 16 of 001 keeps `HOME` for it.
  *Deleting the copied transcripts from `~/.claude/projects`*: deletes in the user's directory for
  tidiness; Claude Code expires them itself (`cleanupPeriodDays`).

## R4. Phase boundaries in the main session

- **Decision**: spec FR-013 gives the spans exactly; a turn is one assistant message (`message.id`),
  since one message spans several transcript entries (R1 2). In short: a phase starts at its first
  worker brief (an Agent call on `sonnet` opening with the phase heading, the rule SC-003 already
  uses) and ends at its first successful `tasks: mark phase <n>`
  commit; from phase 2 on, a phase begins right after the previous marking, so preparing a phase's
  brief belongs to it and every turn falls in exactly one part. A fix hand-off or review inside a span
  belongs to that phase. A worker belongs to the phase its brief's first line names, whatever span its
  call falls in; a review or other subagent belongs to the phase whose span holds its Agent call, or
  to none when that turn is `unattributed`. At the first
  break in the order (a phase never handed off or never marked, a marking before its hand-off, phases
  out of order, two markings in one call followed by a late start), the rest of the session is
  `unattributed`, never folded into a phase; the run still counts, since how the session behaved is
  the feature's to answer for (SC-003), not the measurement's. The setup phase is a phase like the
  others: the fragment hands it to a worker too.
- **Alternatives considered for a break**: *attributing past it phase by phase where possible*:
  every recovery rule is a guess about what the session meant; one rule, "after the first break,
  unattributed", cannot misattribute.
- **`without` and `fallback`**: core gives no phase boundary the harness can rely on (it does not
  commit), so their main session is one part, `main`, beside `review` and `other`. The comparison
  that matters — the `with` main session's per-phase cost against `without`'s whole main session —
  needs no split on `without`.
- **Alternatives considered**: *TodoWrite updates as boundaries*: optional and model-dependent. *Time
  windows between worker calls*: misattributes the verification after a worker to the next phase.

## R5. The new fixture: `checkout`

- **Decision**: a uv Python project whose feature is pricing a shopping cart, in three stories
  after a setup phase — US1 catalog, cart and per-category tax with a stated rounding rule; US2
  promotions (percentage, fixed amount, buy-X-get-Y, a per-order cap) with a stated stacking order and
  exclusivity; US3 returns, refunding a returned line's share of every promotion so that the refunds
  of a fully returned order sum exactly to what was paid (largest-remainder allocation, stated as the
  rule). Each story phase holds 6 to 10 tasks across at least three modules (`money`, `catalog`,
  `cart`, `tax`, `promotions`, `allocation`, `returns`), tests first. Every tie a rule can meet
  (equal discounts between the exclusive and non-exclusive totals, equal remainders in an
  allocation) has a stated tie-break with its own acceptance scenario, so no held-out test rests on
  two readings. Held-out tests: at least one per acceptance
  scenario, written against the interface `plan.md` fixes; a reference implementation proves them.
- **Rationale**: the difficulty is in the spec, as the clarification requires — rules that interact
  (a promotion changes the taxable base; a return unwinds both), edge cases the spec states (a cap
  reached mid-order, a zero-priced free item, a cent left over by allocation) — and money is where a
  careful-reading failure shows as a concrete wrong number, which a held-out test catches without
  judgement. Three modules per phase gives the workers real work to absorb, the size the hypothesis
  needs.
- **Alternatives considered**: *enlarging `wordstats`*: its rules do not interact, so size would add
  turns without adding places to go wrong. *A real feature replayed*: not rerunnable (001 R6).
  *Ambiguity or omitted requirements as difficulty*: rejected by the clarification; it would measure
  luck.
- **Hardening**, if no `without` run misses a held-out test: add stated edge cases and interactions
  to the fixture's spec, with their acceptance scenarios and held-out tests, and their tasks within
  FR-001's ten-task bound per phase; never hide a requirement. At most twice (spec FR-003).

## R6. One harness, two fixtures

- **Decision**: `tests/eval/fixtures/<name>/` holds `project/` (what the agent gets), `heldout/` and
  `reference/`; 001's three directories move to `fixtures/wordstats/` unchanged, the new fixture is
  `fixtures/checkout/`. `run.sh` takes the fixture as its first argument:
  `run.sh <fixture> <arm> <out-dir>`, and records `fixture: <name>` and `arm: <arm>` in
  `versions.txt`.
- **Rationale**: one layout for every fixture, so a third one needs no harness change; 001's exact
  measured state stays on its tag, and its fixture stays runnable on `main`.
- **Alternatives considered**: *`fixture/` kept and `fixture-checkout/` beside it*: two layouts, an
  `if` in the harness. *Keeping the old two-argument call with a default fixture*: an implicit
  default in a measurement tool hides which fixture a result is about.

## R7. Three runs per arm, and the verdict computed

- **Decision** (its interface as finally contracted is `contracts/harness.md`'s `compare.py`, which
  adds `--probes`, `--gate` and `--spent` and judges SC-003, SC-006, SC-007 and SC-008 too, R10): a
  new `tests/eval/compare.py` reads counted run directories, groups them
  by `arm` (and refuses a mix of fixtures, or `versions.txt` that differ but for `date` and `arm`),
  and prints per arm every run's total cost, per-model cost, held-out score and suite result, then
  the median and spread (min, max), the difficulty gate (does any `without` run miss a held-out
  test?), and SC-001, SC-002 and SC-005 judged on medians, with the per-run checks of R10. Exit 0 when
  every one of them holds, 1 when one does not, 2 on unreadable or inconsistent input. The README takes
  its numbers from this output.
- **Rationale**: with nine runs, a verdict worked out by hand is where an error gets in; one script
  computes it the same way every time, and its tests pin the arithmetic (median of three, a 30%
  boundary, a tie on held-out).
- **Alternatives considered**: *the arithmetic in the quickstart, by hand*: as 001 did with three
  numbers; with nine it invites a slip. *A mean*: one outlier run (a retry storm, a cache miss) moves
  it; the median of three does not.

## R8. Order of runs and the deadline

- **Decision**: the three `without` runs go first (they decide the gate); then `with` and `fallback`
  alternate (`with`, `fallback`, `with`, …) so a drift in the service over the session does not land
  on one arm. The agent's deadline stays 3600 s: 001's slowest counted run took 196 s for five tasks,
  so ~30 tasks at the same pace is ~20 minutes, a margin of about three. A run that hits it is not
  counted; the deadline lives in `run.sh`, so raising it is a commit, which changes `versions.txt`
  for every later run, discards every run counted before, and restarts the eval at the `without` set
  under the owner's confirmation (spec Edge Cases).
- **Alternatives considered**: *all of one arm, then the next*: a slow hour lands on a single arm.
  *Fully interleaved, `without` included*: spends `with` runs before the gate has said the fixture is
  worth it.

## R9. Claude Code's auto-updater during the eval

- **Decision**: `run.sh` and `probes.sh` pass `DISABLE_AUTOUPDATER=1` into the clean environment of
  every step (read by Claude Code 2.1.299: the string is in its binary, checked 2026-10-14). The
  variable covers only the eval's own processes; the owner's interactive Claude Code shares the
  binary and can still update it. So `run.sh` writes `versions.txt`'s pre-run keys (commit, tools,
  model, effort, environment, fixture, arm) **before** the agent starts, and with `--baseline
  <run-dir>` refuses the try (exit 2, nothing spent) when they differ from the baseline's; the keys
  only the `init` event reveals (output style, plugins, MCP servers, skills) are compared after the
  run, a difference making it not counted. And before every try the driver (R11) compares the
  installed Claude Code version with the attempt's probes, so the probes, the baseline and every run
  are one version. (The `skills` key lists Spec Kit's project skills and Claude Code's built-in ones;
  checked on 001's `versions.txt` 2026-10-14: none of the user's own skills appear.)
- **Rationale**: nine runs and up to eighteen reruns span hours; an update in the middle would split
  the runs across versions, and the comparison would be refused only after every run was spent.
- **Alternatives considered**: *checking versions only at the end*: finds the split after the spend.
  *Checking after each run and marking a mismatch not counted*: the run's outputs (usage, held-out)
  would already be written, against 001's counting rule, and its cost already spent.
  *Pinning a Claude Code version by path*: the runs would not use the CLI a project uses.

## R10. Committed results and the verdict's two halves

- **Decision**: the run outputs go under `tests/eval/results/002-large-phase-remeasure/` (by feature:
  a date-named directory, tag or README heading would collide with 001's on the same day) as 001's did (no streams, no
  transcripts: local paths and session ids), with `compare.py`'s output and the probes'. The release
  verdict has two halves, both required. `compare.py` judges the gate, SC-001, SC-002, SC-003 (each
  `with` run's `attribution.txt`), SC-005 (medians, and each `fallback` run's `models.txt` and
  `report.txt`), SC-006 (the probes' output, given to it), SC-007 (each `with` run's `models.txt`) and
  SC-008 (each run's `usage.json`). SC-004 stays outside it, observed by hand on the measured commit
  against the core skill and recorded beside its output. The pass condition is `compare.py` exit 0
  and SC-004 holding. Every attempt is committed under `attempt-<k>/`, discarded ones included, so the
  gate's history in the README can be checked against files.
- **Alternatives considered**: *runs only under `/tmp`*: the README's evidence would not survive the
  machine.

## R11. A driver for the sets, not shell in a document

- **Decision**: `tests/eval/runs.sh <attempt-dir> <fixture> <arm>...` runs one confirmed step of the
  eval: three counted runs per named arm, alternating arms per round (`with`, `fallback`, `with`, …),
  each run tried at most three times. Before every try it refuses unless the attempt's `probes.txt`
  exists with every probe `ok` and its Claude Code version equals the installed one; it passes the
  attempt's first counted `without` run as `--baseline`; and for `with` or `fallback` it refuses unless
  `compare.py --gate` is open on the attempt's `without` runs. It stops at the first refusal or at a
  run with no counted try, and its exit code says which. State lives in the attempt directory, so each
  step is one command and nothing depends on a shell surviving between steps; directory walks are in
  Python (`compare.py --spent <root>`), so no shell glob can fail on an empty match.
- **Rationale**: the third review of the checklist found the quickstart's shell would abort in zsh on
  the first spend query, lose its state between confirmations, close an interactive shell with
  `exit`, and check the probes' version only after every run was paid for. A script with tests fixes
  all four and keeps the owner's confirmations as the boundaries between its invocations.
- **Alternatives considered**: *fixing the snippets*: still untested shell in a document, run by
  hand, where the next slip costs a run. *One script that runs the whole eval*: it would have to stop
  for confirmations anyway; one invocation per confirmed step makes each confirmation the act of
  running it.
