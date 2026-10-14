# Contract: the fragment and the eval harness

## `commands/speckit.implement.md`, appended to core `speckit-implement`

A section `## Story workers`. `tests/compose.sh` greps the composed skill (joined into one line
first, so rewrapping does not fail it) for each quoted phrase, and greps core for each narrowed rule
and each step the brief names.

1. **Unit**: "hand each phase to a worker", in the order core runs the phases; the next only after
   the previous one's verification; never two at once; `[P]` tasks run inside their phase's worker.
   Narrows core's `parallel tasks [P] can run together`.
2. **The call**: `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"`.
3. **The brief**: the phase's tasks (or a fix's finding), the feature directory, the suite and
   static-check commands (the project's instructions, else `plan.md`'s Technical Context), what
   earlier workers finished, and "follow core's" `Project Setup Verification` (first phase only),
   `Execute implementation`, `Implementation execution rules` and `Progress tracking and error
   handling` steps of `.claude/skills/speckit-implement/SKILL.md`. The worker "commits each task",
   and does not edit `tasks.md`, start a review or start a worker.
4. **The report**: first and last commit; tasks done; for each task not done, what stopped it;
   anything found that no task covers; the output of its last whole-suite run.
5. **Verification**: before the phase's first worker, the main session records HEAD and runs the
   static checks as the baseline. It "marks a task [X] only after" its own runs show the whole suite
   passing, nothing beyond the baseline, and the commits from the recorded HEAD changing only files
   (or directories) the phase's tasks name, with nothing uncommitted. Narrows core's `For completed
   tasks, make sure to mark the task off as [X]`.
6. **Hand-offs**: every unfinished task, failed verification or review finding goes to a worker,
   then verification again. A hand-off that resolves none of what it was given gets one more worker;
   the second "stops and reports". A usage limit stops and reports at once. The main session writes
   only `tasks.md` (checkboxes, tasks a worker reported finding) and commits it.
7. **Reviews**: any review the project or a command calls for, "with `model` set to this session's
   model family" and no `effort`, in a fresh context, never a worker.
8. **Hooks**: a call a project hook blocks is the worker's to resolve or report; the main session
   never makes it itself.
9. **Fallback**: no Agent tool, or the first Agent call returns an error and no report for a reason
   other than a usage limit: "carry out the tasks in this session" as core does, and say so in the
   completion report.
10. **Resume**: commits with unmarked tasks are verified as in 5; uncommitted changes go to a worker
    with the diff, to finish or discard.

## `tests/eval/run.sh <without|with|fallback> <out-dir>`

- Refuses: an unknown arm, an existing `<out-dir>`, uncommitted changes in this checkout, a missing
  `claude`, `specify`, `uv`, `git`, `python3` or `jq`.
- Builds a scratch copy of `fixture/`, `git init`, `specify init --here --force --integration
  claude`; for `with` and `fallback`, installs this checkout's `git archive` of HEAD served from
  localhost; commits.
- Runs, under a deadline that kills its process group:
  `env -u CLAUDE_CODE_SUBAGENT_MODEL -u CLAUDE_CODE_EFFORT_LEVEL claude -p "/speckit-implement"
  --model claude-opus-5-5 --effort medium --setting-sources project,local --strict-mcp-config
  --allowedTools "Agent Bash Edit Write Read Glob Grep TodoWrite" --output-format stream-json
  --verbose`, plus `--disallowedTools Agent` for `fallback`.
- Counts the arm only when `claude` exited 0 within the deadline, the stream holds exactly one
  `result` event and it has `is_error: false`; for `with`, `modelUsage` has a Sonnet entry and every
  commit after the setup commit starts with `fixture:`; for `fallback`, `modelUsage` has only the
  main model. Otherwise writes `status` with the reason, no `usage.txt` or `heldout.txt`, and exits 1.
- On a counted arm: copies `heldout/` in and runs it (`heldout.txt`: passed/total and the output),
  runs the project's own suite (`suite.txt`), writes `usage.txt` (each model's `costUSD`, the sum),
  `versions.txt` (date; Claude Code, Spec Kit, git, uv, Python, pytest; model IDs; the `init` event's
  skills and plugins) and `status` = `ok`.

## `tests/eval/attribution.py <out-dir>`

Reads `stream.jsonl`. Prints the main session's (no `parent_tool_use_id`) Write, Edit and
NotebookEdit calls whose path is not the feature's `tasks.md`, then its Bash commands. Exit 0 when
the first list is empty, 1 when not, 2 when the stream cannot be read or `status` is not `ok`.
