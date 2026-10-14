# Data model: Large-phase remeasure

## Fixture (`tests/eval/fixtures/<name>/`)

| Part | Holds | Rule |
|---|---|---|
| `project/` | what the agent gets: a uv project, `CLAUDE.md`, `.specify/feature.json`, `specs/001-<name>/{spec,plan,tasks}.md`, `uv.lock` | copied as git tracks it; no `checklists/` (core's gate would stop a headless run) |
| `heldout/` | acceptance tests, copied in only after a counted run | each test's docstring names its scenario (`US<n>-<m>`) and quotes the spec text its expected values follow from; each scenario has ≥1 |
| `reference/` | a correct implementation | every held-out test passes against it (the oracle proof) |

`checkout`'s `tasks.md`: `Phase 1: Setup`, then exactly three user-story phases, each of 6 to 10
task lines (test-writing tasks included), tests first; each task names its files. `CLAUDE.md` is
`wordstats`'s with only the name, description line and spec path changed (spec FR-001). The
fixture's held-out N is recorded in `heldout/N` (one integer: the tests collected against
`reference/` by the oracle proof).

## Attempt directory (`<attempt-dir>/`, one per attempt)

```text
probes/  probes.txt                 # step 0, every attempt
<arm>-<n>-<try>/                    # one per try (run directory below)
<arm>-<n> -> <arm>-<n>-<try>        # the counted try of run n (a relative link)
gate.txt                            # compare.py --gate output
compare.txt  sc004.txt              # only in the attempt that reaches a verdict
```

## Run directory (`<arm>-<n>-<try>/`)

001's files (contract 001 `run.sh`), plus:

| File | Content |
|---|---|
| `versions.txt` | pre-run keys (`commit`, `claude`, `specify`, `git`, `uv`, `main_model`, `main_effort`, `environment`, `git_isolation`, `fixture`, `arm`, `autoupdater: disabled`) written before the agent starts, none of them touching the scratch repository; post-run keys (`python`, `pytest`, `ruff` — read through `uv run` in the scratch repository, as 001 did after the run — and the `init`-event keys `output_style`, `plugins`, `mcp_servers`, `skills`) and `date` added after |
| `transcripts/` | the run's main transcript `<session_id>.jsonl` and `subagents/agent-*.{jsonl,meta.json}`, copied whenever the stream names a session; never committed (local paths, session ids) |
| `usage.txt` | per model: cost, input, output, cache read, 5m write, 1h write; `sum`; `five_hour`; `reconciled yes`; one line per part |
| `usage.json` | the same, machine-readable, for `compare.py` |

A run that does not reconcile, or whose `init`-event keys differ from the baseline's, is not counted:
its `status` is `not counted: <reason>`, and it has no `usage.*`, `suite.txt` or `heldout.txt` (001's
rule for a run that does not count).

## Usage attribution (`usage.json`)

```text
models:   {<model id>: {reported: Tokens + {cost},       # modelUsage
                        transcripts: Tokens + {cost}}}  # summed and priced; equal, within SC-008
parts:    [{part, phase|null, model, Tokens, cost}]
Tokens:   input, output, cache_read, cache_write_5m, cache_write_1h
```

- A **turn** is one assistant message: transcript entries merged by `message.id`, the last entry's
  usage counted once.
- `part` ∈ `main` (`without`, `fallback`); `before`, `phase`, `after`, `unattributed` (the `with` main
  session, spans as spec FR-013); `worker`, `review`, `other` (subagents, by their meta file:
  `model: sonnet` → `worker`; `agentType: general-purpose` with any other model or none → `review`;
  any other `agentType` → `other`).
- A worker's `phase` is the phase its brief's first line names, `null` when it names none; a review's
  or other's is the phase whose span holds its Agent call, `null` when that turn is outside every
  phase or its `toolUseId` matches no Agent call in the main transcript.
- Invariant: per model and token type, `transcripts` equals `reported` and the parts' tokens sum
  exactly to it; `transcripts.cost` and the parts' summed cost are each within $0.000001 of
  `reported.cost` (floating-point rounding of prices). Both halves of SC-008 can thus be re-judged
  from the committed `usage.json`.
- Reconciliation reasons (each makes the run not counted): `no transcript`, `unreadable <file>`,
  `<model> <field> transcript=<n> reported=<n>`, `<model> cost priced=<usd> reported=<usd>`,
  `<model> price unknown`.

## Held-out score

`passed / N`, where `N` is `fixtures/<fixture>/heldout/N` (fixed per fixture, written by the
oracle proof); an error, a skip or an uncollected test is not passed. `heldout.txt`'s `passed x/y`
gives `x`; `y` is not used, since a module that fails to collect shrinks it.

## Comparison (`compare.py` output)

Per arm: each run's directory, total cost, cost per model, held-out score, suite exit; then `median`
and `min`/`max` of total cost and of held-out score. Then:

- `gate`: `open` when at least one `without` run's score is below `N`, else `closed`.
- `SC-001`: `1 - median(with) / median(without) >= 0.30` on total cost.
- `SC-002`: `median(with score) >= median(without score)`, and every `with` suite exit is 0.
- `SC-003`: every `with` run's `attribution.txt` has every clause `ok`.
- `SC-005`: `median(fallback score) >= median(without score)`; every `fallback` run's `models.txt`
  shows no Agent call and its `report.txt` lists, after `Carried out in this session:`, every task id
  of `fixtures/<fixture>/project/`'s feature `tasks.md`.
- `SC-006`: the probes' output has every probe `ok`, and the version in its `claude` line equals every
  run's `versions.txt` `claude:` (compared as `major.minor.patch`).
- `SC-007`: in every `with` run's `models.txt`, the count of `general-purpose`/`opus` calls is at
  least the number of `### User Story` headings in `fixtures/<fixture>/project/`'s feature spec (the
  `fixture` key), so committed results can be re-judged without the scratch repository.
- `SC-008`: every run's `usage.json` exists and satisfies the invariant.

Refused (exit 2): a run whose `status` is not `ok`, an arm without exactly three runs, runs of
different fixtures, or `versions.txt` that differ in any key but `date` and `arm`.

## Spend (`compare.py --spent <root> [--next <arm>...]`)

Walks `<root>` for every `*.jsonl` outside `transcripts/` that holds a stream (a run's
`stream.jsonl`, each probe's `r*.jsonl`): each one's `result` `costUSD`, else its copied transcripts
priced at the table (`usage.py --price-only`), else zero with `no cost recorded`.
Prints per try and the total; with `--next`, the estimate summed over the named arms (spec FR-008)
and the worst case, three times it. Before any run has counted on the fixture, the per-run figure is
001's `without` cost (`tests/eval/results/2026-10-14/without/usage.txt`, its `sum` line) times the
ratio of task lines in `fixtures/<fixture>/project/`'s feature `tasks.md` to those in
`fixtures/wordstats/project/`'s.
