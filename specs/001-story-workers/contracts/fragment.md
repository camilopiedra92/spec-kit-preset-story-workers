# Contract: the fragment, the eval harness and the probes

## `commands/speckit.implement.md`, appended to core `speckit-implement`

A section `## Story workers`. `tests/compose.sh` greps the composed skill (joined into one line
first, so rewrapping does not fail it) for each quoted phrase as a fixed string (`grep -F`: `[X]`
and `[P]` are not character classes), and greps core for each narrowed rule
and each step the brief names.

1. **Unit**: "hand each phase to a worker", in the order core runs the phases; the next only after
   the previous one's verification; never two at once; `[P]` tasks run inside their phase's worker.
2. **The call**: `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"`.
3. **The brief** (spec FR-003): the phase's tasks, and for a fix the finding, on resume the
   uncommitted diff; the feature directory; the suite and static-check commands (the project's
   instructions, else `plan.md`'s Technical Context); what earlier workers finished; "follow core's"
   `Load and analyze the implementation context`, `Project Setup Verification` (first phase only),
   `Execute implementation`, `Implementation execution rules` and `Progress tracking and error
   handling` steps of `.claude/skills/speckit-implement/SKILL.md`; the worker "commits each task",
   returns the report of 4, follows or reports a call a project hook blocks, and does not edit
   `tasks.md` (core's "mark the task off as [X]" in those steps is the main session's), start a
   review or start a worker.
4. **The report**: first and last commit; tasks done; for each task not done, what stopped it;
   anything found that no task covers; the output of its last whole-suite run.
5. **Verification**: before the phase's first worker, the main session records HEAD and runs the
   static checks as the baseline. It "marks a task [X] only after" its own runs show the whole suite
   passing and no static-check finding the baseline lacked, and its reading of the diff from the
   recorded HEAD finds nothing the phase's tasks do not call for (suite and checks when named). A
   review the phase calls for, and its fixes, resolve first; then it commits `tasks.md` as
   `tasks: mark phase <n>`, and only then starts the next phase's worker.
6. **Hand-offs**: every unfinished task, failed verification or review finding goes to a worker,
   then verification again; a review finding passes when a fresh review of it no longer reports it.
   A phase gets "at most two fix hand-offs"; when verification still fails after them, "carry out
   the phase's remaining items in this session". Tasks a worker reported finding join the current
   phase (committed as `tasks: add found tasks`) and go to its next hand-off. "Verification still
   fails" includes a fresh review still reporting its finding. The main session's only edits to tracked files are `tasks.md` (checkboxes, tasks a
   worker reported finding) and its commits of them.
7. **Reviews**: any review the user's or the project's instructions, or a command, call for, `subagent_type: "general-purpose"`,
   "with `model` set to this session's model family" and no `effort`, in a fresh context, never a
   worker; with no fresh context possible, the review does not run and the report says so.
8. **Hooks**: a call a project hook blocks is the worker's to follow or report; the main session
   never makes it itself, also in the fallback: the task is not handed off again, stays unmarked, is
   reported, and the next phase starts without it.
9. **Fallback**: no Agent tool, a worker's error (a usage limit included) or missing report, or the
   bound of 6: "carry out the remaining tasks in this session" as core does, and say which and why in
   the completion report. The completion report always carries the line `Carried out in this session:
   none` or `Carried out in this session: <task ids>`; `tests/compose.sh` greps for it.
10. **Resume**: the phase starts after the last `tasks: mark phase <n>` commit; the baseline is
    taken there, in a temporary `git worktree`; uncommitted changes to files other than `tasks.md` go to
    a worker with the diff, to finish or discard; uncommitted `tasks.md` changes are the main session's.
11. **Narrowed, by name**: core's `For completed tasks, make sure to mark the task off as [X]`,
    `parallel tasks [P] can run together` and `Halt execution if any non-parallel task fails`.

## `tests/eval/run.sh <without|with|fallback> <out-dir>`

- Refuses: an unknown arm, an existing `<out-dir>`, uncommitted changes in this checkout, a missing
  `claude`, `specify`, `uv`, `git`, `python3` or `jq`.
- Builds a scratch copy of `fixture/` (which carries its `uv.lock` and `.specify/feature.json`),
  `git init`, `specify init --here --force --integration claude`, checks `.specify/feature.json`
  survived; for `with` and `fallback`, installs this checkout's `git archive` of HEAD served from
  localhost, with `SPECKIT_PYTHON_EXECUTABLE` set; commits.
- Every step after the refusals — the setup commit, the agent, the suite and the held-out run — runs
  in the same clean environment: `env -i` passing only `HOME`, `USER`, `LOGNAME`, `PATH`, `TMPDIR`,
  `LANG`, `TERM` and `SPECKIT_PYTHON_EXECUTABLE`, then setting only git's isolation (`GIT_CONFIG_GLOBAL=/dev/null`,
  `GIT_CONFIG_NOSYSTEM=1`, a fixed `eval` identity) — under a 3600-second deadline enforced by
  `tests/eval/bounded.py`, which runs the command in its own process group and kills the group (macOS
  ships no `timeout`): `claude -p "/speckit-implement" --model
  claude-opus-5-5 --effort medium --setting-sources project,local --strict-mcp-config --allowedTools
  "Agent Bash Edit Write Read Glob Grep TodoWrite" --output-format stream-json --verbose`, plus
  `--disallowedTools Agent` for `fallback`. The environment and git settings are written to
  `versions.txt`.
- Counts the arm only as research.md R6 "Counting" says; otherwise writes `status` with the reason,
  no `usage.txt` or `heldout.txt`, and exits 1. A refusal writes nothing and exits 2: it is fixed, not
  retried. Reruns are the caller's (quickstart).
- On a counted arm: runs the project's suite (`suite.txt`), then copies `heldout/` to
  `tests_heldout/` and runs it alone (`heldout.txt`: passed/total and the output); writes
  `usage.txt`, `versions.txt` (this checkout's commit, tools, the main model ID and its effort, the `init` event's output
  style, plugin and MCP-server counts), `models.txt` (every model ID in `modelUsage` with its effort, and
  the Agent calls per `model` value)
  and `status` = `ok`.

## `tests/eval/attribution.py <out-dir>`

Reads `stream.jsonl`. Prints the main session's (no `parent_tool_use_id`) Write, Edit and
NotebookEdit calls whose path is not the feature's `tasks.md`, then its Bash commands. Exit 0 when
the first list is empty, 1 when not, 2 when the stream cannot be read or `status` is not `ok`.

## `tests/eval/probes.sh`

Reruns R1 (1, 3, 4 with both `sonnet` and `opus`, 5, 7, 8, 9, 10, 11, 15) headless and hermetic in
scratch repositories, prints the Claude Code version and one line per probe (`ok` or `FAIL` with what was seen), and exits 1 when any fails. Probe 5 and 8 compare
thinking tokens between a low and a high effort on the call, and fail when the high arm's is not
larger.
