# Contract: the harness after 002

001's contract (`specs/001-story-workers/contracts/fragment.md`) holds for the fragment and
`attribution.py`, unchanged. For `run.sh` and `probes.sh` it holds but for the deltas below.

## `tests/eval/run.sh [--baseline <run-dir>] <fixture> <arm> <out-dir>`

- `<fixture>` names a directory under `tests/eval/fixtures/`; refused (exit 2) when it does not
  exist or lacks `project/` or `heldout/`.
- The scratch repository is a copy of `fixtures/<fixture>/project/` as git tracks it; the held-out
  tests come from `fixtures/<fixture>/heldout/`.
- The clean environment adds `DISABLE_AUTOUPDATER=1` to every step.
- `versions.txt`'s pre-run keys (data model) are written after setup and **before the agent
  starts**; with `--baseline`, a difference from the baseline's pre-run keys other than `arm` refuses
  the try (exit 2, the agent never starts), naming the keys. After the run, the `init`-event keys and `date` are
  added; with `--baseline`, an `init`-event key differing from the baseline's makes the run not
  counted.
- Whenever the stream's `init` event names a `session_id`, whatever the agent's exit, the run's
  transcripts (`$HOME/.claude/projects/*/<session_id>.jsonl` and its `<session_id>/subagents/`) are
  copied into `<out-dir>/transcripts/`.
- Counting adds, after 001's checks and the `init`-key comparison, before the suite: `usage.py
  <out-dir>`. Its exit 1 makes the run not counted (`status`: `not counted: unreconciled: <reasons>`,
  exit 1, no `usage.*`, `suite.txt` or `heldout.txt`). Its exit 2 is a harness fault: `status`:
  `refused: harness fault: <message>`, exit 2.
- 001's `usage.txt` block (jq over `modelUsage`) is removed: `usage.py` writes `usage.txt`.
- Exit codes are 001's: 0 counted, 1 not counted (rerun within the bound), 2 refused (stop and fix).

## `tests/eval/usage.py [--price-only] <out-dir>`

Reads `stream.jsonl` (the `result` event's `modelUsage`, the `rate_limit_event`s), `transcripts/`,
`versions.txt` (`arm`, `fixture`), and for `with` the phase headings from
`fixtures/<fixture>/project/`'s feature `tasks.md`. Reconciles (data model). When reconciled, writes
`usage.json` and `usage.txt` and exits 0:

```text
<model> cost <usd> input <n> output <n> cache_read <n> cache_write_5m <n> cache_write_1h <n>
sum <usd>
five_hour <first> <last>
reconciled yes
part <part> phase <n|-> <model> cost <usd> input <n> output <n> cache_read <n> cache_write_5m <n> cache_write_1h <n>
```

When not — a mismatch, or a transcript or stream line that cannot be parsed (`unreadable <file>`) —
writes nothing, prints `unreconciled: <reason>[; <reason>...]` (data model) and exits 1. Exit 2 is
reserved for a fault in `usage.py` itself (an unexpected exception). `--price-only` prints `spent <usd>`, the transcripts'
cost at the price table, and nothing else.

Prices: one table in `usage.py` with its source URL and the date read (research R1 4). A model with
no price is `<model> price unknown`, never guessed.

## `tests/eval/runs.sh <attempt-dir> <fixture> <arm>...`

One confirmed step (research R11): three counted runs per named arm, arms alternating per round. Per
try, in order, it refuses (exit 2, nothing started) unless: `<attempt-dir>/probes.txt` exists with
every probe `ok` and the same Claude Code version as `claude --version` now; for `with` or
`fallback`, `compare.py --gate` is open on `<attempt-dir>/without-?`. It calls `run.sh` with
`--baseline <attempt-dir>/without-1` once that exists, into `<attempt-dir>/<arm>-<n>-<try>`, and links
`<arm>-<n>` to the counted try with a relative link. Every refusal, its own or `run.sh`'s, leaves the
try's directory with a `status` of `refused: <reason>`. Exit 0 when every run counted; 1 when a run had three tries without
counting (the eval stops: spec US3 scenario 3); 2 on any refusal, `run.sh`'s included.

## `tests/eval/compare.py`

- `compare.py --probes <probes.txt> <run-dir>...`: refused input (exit 2) as the data model says.
  Prints, per arm, each run and the median and spread, then `gate`, `SC-001`, `SC-002`, `SC-003`,
  `SC-005`, `SC-006`, `SC-007` and `SC-008`, each `ok` or `FAIL` with its numbers. Exit 0 when the gate
  is open and every one holds, 1 otherwise.
- Held-out N comes from `fixtures/<fixture>/heldout/N` (data model, "Held-out score").
- `compare.py --gate <without-run-dir>...`: three counted `without` runs; prints the scores and
  `gate open` (exit 0) or `gate closed` (exit 1); 2 on refused input.
- `compare.py --spent <root> [--next <arm>...]`: the data model's "Spend". Exit 0; 2 on unreadable
  input. An empty root prints `spent 0`.

## `tests/eval/probes.sh [out-dir]`

As 001, plus `DISABLE_AUTOUPDATER=1` in its clean environment. Its `claude <version> (Claude Code)`
line (already printed) carries the version `runs.sh` and `compare.py --probes` compare as
`major.minor.patch`.
