# Quickstart: running the eval

Requires `claude` signed in, `specify`, `uv`, `git`, `python3` and `jq`, and this checkout committed.
The probes cost cents; each eval arm runs a full `/speckit-implement` on Opus and spends real usage.
Run everything back to back on one machine. Runs are hermetic: your own instructions, settings,
hooks, skills, plugins and MCP servers do not load.

```bash
tests/eval/probes.sh                                   # SC-006: every probe ok
for arm in without with fallback; do
  for try in 1 2 3; do                                 # one counted run; rerun at most twice
    tests/eval/run.sh "$arm" "/tmp/eval-$arm-$try" && ln -sfn "eval-$arm-$try" "/tmp/eval-$arm" && break
  done
done
cat /tmp/eval-*-*/status                               # every try, with each rerun's reason
cat /tmp/eval-{without,with,fallback}/usage.txt        # costUSD per model, the sum, the window
cat /tmp/eval-{without,with,fallback}/heldout.txt      # held-out passed / total
uv run python tests/eval/attribution.py /tmp/eval-with # SC-003: exit 0
for arm in with fallback; do                           # same tools and main model, or rerun
  diff <(grep -v '^date' /tmp/eval-without/versions.txt) <(grep -v '^date' "/tmp/eval-$arm/versions.txt")
done
cat /tmp/eval-{without,with,fallback}/models.txt      # models, efforts and Agent calls, per arm
```

- **SC-001**: `1 - with.sum / without.sum >= 0.30`.
- **SC-002**: `with` passes at least as many held-out tests as `without`, and its `suite.txt` is green.
- **SC-005**: `fallback` passes at least as many held-out tests as `without`, and its last message
  says the tasks ran in the session.
- Record in the README: the date, the fixture's size, every arm's outputs, any rerun and its reason,
  `versions.txt`, the probes' output, the isolation used, and "one counted run per arm, directional".
