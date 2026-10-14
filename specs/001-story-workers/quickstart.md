# Quickstart: running the eval

Requires `claude` signed in, `specify`, `uv`, `git`, `python3` and `jq`, and this checkout committed.
Each arm runs a full `/speckit-implement` on Opus and spends usage; run them back to back on one
machine. The runs are hermetic: your own instructions, settings, hooks and MCP servers do not load.

```bash
for arm in without with fallback; do tests/eval/run.sh "$arm" "/tmp/eval-$arm"; done
cat /tmp/eval-*/status                                        # each must say ok
cat /tmp/eval-*/usage.txt                                     # costUSD per model, and the sum
cat /tmp/eval-*/heldout.txt                                   # held-out passed / total
uv run python tests/eval/attribution.py /tmp/eval-with        # SC-003: exit 0
diff <(grep -v '^date' /tmp/eval-without/versions.txt) <(grep -v '^date' /tmp/eval-with/versions.txt)
```

- **SC-001**: `1 - with.sum / without.sum >= 0.30`.
- **SC-002**: `with` passes at least as many held-out tests as `without`, and its `suite.txt` is green.
- **SC-005**: `fallback` passes at least as many held-out tests as `without`, and its last message
  says the tasks ran in the session.
- Record every arm in the README: the date, the fixture's size, the outputs above, `versions.txt`,
  the isolation used, and "one run per arm, directional".
