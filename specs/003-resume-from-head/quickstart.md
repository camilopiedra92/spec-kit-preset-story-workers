# Quickstart: the resume eval

Before: `tests/check.sh` green; `tests/eval/probes.sh "$A/probes" > "$A/probes.txt"` all ok;
`tests/eval/oracle.sh checkout` passes; the owner has confirmed the spend (one `with` run, about $2,
priced from 002's runs).

```bash
A=/tmp/resume-eval; mkdir -p "$A"
tests/eval/run.sh --state phase-2-done checkout with "$A/with-1"   # rerun at most twice if not counted
uv run python tests/eval/attribution.py "$A/with-1" > "$A/with-1/attribution.txt"
uv run python tests/eval/resume_check.py "$A/with-1" | tee "$A/with-1/resume.txt"
```

Passes when `resume_check.py` exits 0. Record: copy the run's committed files (no stream, no
transcripts) to `tests/eval/results/003-resume-from-head/`, write the README's Eval 003 entry, then
release `0.2.0`.
