# Contract: the fragment and the eval harness

## `commands/speckit.implement.md`, appended to core `speckit-implement`

A section `## Story workers`. `tests/compose.sh` greps the composed skill (joined into one line
first, so rewrapping does not fail it) for each quoted phrase, and core for each narrowed rule.

1. **Unit**: "hand each phase to a worker", in the order core runs the phases; the next only after
   the previous one's verification; never two workers at once; `[P]` tasks run inside their phase's
   worker one after another. Narrows core's `parallel tasks [P] can run together`.
2. **The call**: `subagent_type` `"general-purpose"`, `model: "sonnet"`.
3. **The brief**: the phase's tasks, the feature directory, the project's suite and static-check
   commands, what earlier workers finished, and "follow the Execute implementation, Implementation
   execution rules and Progress tracking and error handling steps" of
   `.claude/skills/speckit-implement/SKILL.md`; the worker does not mark a checkbox, start a review or
   start a worker. A fix's brief carries the finding.
4. **The report** the worker returns: tasks done and not done, anything found that no task covers,
   the output of its last whole-suite run.
5. **Verification**: "mark a task [X] only after" the main session's own runs show the whole suite
   passing, the static checks reporting nothing new, and the phase's commits changing nothing
   outside the phase's tasks. Narrows core's `For completed tasks, make sure to mark the task off as
   [X]`.
6. **Unfinished and fixes**: one new worker for unfinished tasks; "stop and report" when it makes no
   progress or a worker's error is a usage limit; every fix to a worker, then verification again.
7. **Reviews**: any review the project or a command calls for, "with `model` set to this session's
   own model", in a fresh context, never a worker.
8. **Fallback**: no Agent tool, or the call errors before the worker's first tool call: "carry out
   the tasks in this session" as core does, and say so in the completion report.
9. **Resume**: a phase with commits but unmarked tasks is verified as in 5, then the rest handed on.

## `tests/eval/run.sh <with|without> <out-dir>`

- Refuses: an unknown arm, an existing `<out-dir>`, uncommitted changes in this checkout, a missing
  `claude`, `specify`, `uv`, `git` or `jq`.
- Builds a scratch copy of `fixture/`, `git init`, `specify init --here --force --integration
  claude`; for `with`, installs this checkout's `git archive` of HEAD served from localhost; commits.
- Runs `claude -p "/speckit-implement" --model claude-opus-5-5 --output-format stream-json
  --verbose --allowedTools <the tools implement needs>` under a deadline that kills its process
  group.
- Then copies `heldout/` in and runs it; runs the project's own suite.
- Writes `stream.jsonl`, `usage.txt` (each model's `costUSD` and the sum, from the one `result`
  event; fails unless there is exactly one), `heldout.txt`, `suite.txt`, `versions.txt` (Claude
  Code, Spec Kit, git, uv, pytest).

## `tests/eval/attribution.py <out-dir>`

Reads `stream.jsonl`. Prints the main session's (no `parent_tool_use_id`) Write, Edit and
NotebookEdit calls whose path is not the feature's `tasks.md`, then its Bash commands. Exit 0 when
the first list is empty, 1 when not, 2 when the stream cannot be read.
