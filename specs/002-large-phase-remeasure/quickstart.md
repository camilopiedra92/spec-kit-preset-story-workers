# Quickstart: running the remeasure

Requires what 001's quickstart lists (`claude` signed in, `specify`, `uv`, `git`, `python3`, `jq`,
this checkout committed). Every set of runs spends real usage and starts only after the owner
confirms it (spec FR-008). Each numbered step is one command or a short sequence; **STOP** marks a
confirmation, and nothing runs past one on its own. State lives in the attempt directory, so each
step can run in a fresh shell.

Attempt *k* (the first, or after a hardening, a harness change or a Claude Code version change) uses
its own directory; nothing from a discarded attempt is reused. Every step below starts with

```bash
A=/tmp/remeasure/attempt-<k>; mkdir -p "$A"
```

## 0. Before every attempt

```bash
tests/check.sh                                              # green
tests/eval/probes.sh "$A/probes" > "$A/probes.txt"          # every probe ok, else STOP
```

```bash
tests/eval/oracle.sh checkout                               # every held-out test passes, count = N
```

Plus the fresh-context review of the held-out tests, recorded in
`specs/002-large-phase-remeasure/heldout-review.md` with every finding closed (spec FR-002); after a
hardening, the review covers what it added.

## 1. `without`: the gate

```bash
uv run python tests/eval/compare.py --spent /tmp/remeasure --fixture checkout --next without
```

**STOP**: the owner confirms the `without` set: spend so far, estimate, worst case.

```bash
tests/eval/runs.sh "$A" checkout without
uv run python tests/eval/compare.py --gate "$A"/without-? | tee "$A/gate.txt"
```

`gate closed`: harden the fixture (research R5), commit, and start attempt *k*+1 at step 0, at most
twice; a third closed gate ends the eval as not measured (spec US3 scenarios 5 and 6). `runs.sh`
exit 1: the eval stops, not measured. Exit 2: read the try's `status`. A refusal that spent nothing
(a dirty tree, a missing or failed probes file) is fixed and the same command run again in the same
attempt; a harness fault (fixed and committed) or a Claude Code version change starts a new attempt
at step 0.

## 2. `with` and `fallback`, alternating

```bash
uv run python tests/eval/compare.py --spent /tmp/remeasure --fixture checkout --next with fallback
```

**STOP**: the owner confirms the `with` and `fallback` sets together.

```bash
tests/eval/runs.sh "$A" checkout with fallback
for n in 1 2 3; do
  uv run python tests/eval/attribution.py "$A/with-$n" > "$A/with-$n/attribution.txt"
done
uv run python tests/eval/compare.py --probes "$A/probes.txt" "$A"/without-? "$A"/with-? \
  "$A"/fallback-? | tee "$A/compare.txt"
```

SC-004, outside `compare.py`: `tests/compose.sh` on the measured commit removes each anchored core
rule and step from a copy of the **core** `speckit-implement` skill and fails unless
`tests/core-anchors.sh` goes red naming it:

```bash
tests/compose.sh > "$A/sc004.txt" 2>&1                      # ends with `ok: composes on specify …`
```

**The eval passes** when `compare.py` exits 0 and SC-004 holds; otherwise it fails.

## 3. Record

Copy every attempt into `tests/eval/results/002-large-phase-remeasure/attempt-<k>/` as spec FR-012
lists, never streams or transcripts. The README entry, `Eval 002, <date>`, takes every field spec
FR-009 lists. Pass: spec US3 scenario 1, then FR-010. Fail: US3 scenario 2, tag
`measured-not-adopted-002-<date>`. Stopped without a verdict: US3 scenario 6. Either of the last two
accepted for release by the owner (constitution III, v2.0.0): US3 scenario 7, then FR-010.
