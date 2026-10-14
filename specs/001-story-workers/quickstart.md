# Quickstart: running the eval

Requires `claude` signed in, `specify`, `uv`, `git` and `jq`, and this checkout committed. Each arm
runs a full `/speckit-implement` on Opus and spends usage; run them back to back on one machine.

```bash
tests/eval/run.sh without /tmp/eval-without
tests/eval/run.sh with    /tmp/eval-with

cat /tmp/eval-without/usage.txt /tmp/eval-with/usage.txt       # costUSD per model, and the sum
cat /tmp/eval-without/heldout.txt /tmp/eval-with/heldout.txt   # held-out passed / total
uv run python tests/eval/attribution.py /tmp/eval-with         # SC-003: exit 0
diff /tmp/eval-without/versions.txt /tmp/eval-with/versions.txt  # must be empty
```

- **SC-001** holds when `1 - with.sum / without.sum >= 0.30`.
- **SC-002** holds when `with` passes at least as many held-out tests as `without`, and its
  `suite.txt` is green.
- Record both arms in the README: the fixture's size, the outputs above, `versions.txt`, and "one run
  per arm, directional".
