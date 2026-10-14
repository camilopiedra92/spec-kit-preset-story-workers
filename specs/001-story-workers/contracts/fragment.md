# Contract: the fragment, the eval harness and the probes

## `commands/speckit.implement.md`, appended to core `speckit-implement`

A section `## Story workers`. `tests/compose.sh` greps the fragment (joined into one line first, so
rewrapping does not fail it; its tail check has already tied the composed skill to the fragment, and
core's own text would satisfy a grep of the narrowed rules on the composed skill) for each quoted phrase as a fixed string (`grep -F`: `[X]`
and `[P]` are not character classes). `tests/core-anchors.sh <skill-file>` greps a core skill the
same way for each narrowed rule and each step the brief names, and exits 1 naming any missing;
`tests/compose.sh` runs it on core's skill as installed, before the preset is added.

1. **Unit**: "hand each phase to a worker", in the order core runs the phases; the next only after
   the previous one's verification; never two at once; `[P]` tasks run inside their phase's worker.
2. **The call**: `subagent_type: "general-purpose"`, `model: "sonnet"`, `effort: "medium"`,
   `run_in_background: false`.
3. **The brief** (spec FR-003): "opens with the phase's heading" as `tasks.md` writes it; the phase's tasks, and for a fix the finding, on resume the
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
   review the phase calls for, and its fixes, resolve first; then it commits `tasks.md` with a
   message containing `tasks: mark phase <n>` (after any prefix the project requires), and only then starts the next phase's worker.
6. **Hand-offs**: every unfinished task, failed verification or review finding goes to a worker,
   then verification again; a review finding passes when a fresh review of it no longer reports it.
   A phase gets "at most two fix hand-offs" (every hand-off of the phase after its first counts); when verification still fails after them, "carry out
   the phase's remaining items in this session". Tasks a worker reported finding join the current
   phase (committed with a message containing `tasks: add found tasks`) and go to its next hand-off. "Verification still
   fails" includes a fresh review still reporting its finding. The main session's only edits to tracked files are `tasks.md` (checkboxes, tasks a
   worker reported finding) and its commits of them.
7. **Reviews**: any review the user's or the project's instructions, or a command, call for, `subagent_type: "general-purpose"`,
   "with `model` set to this session's model family" and no `effort`, in a fresh context, never a
   worker; with no fresh context possible, the review does not run and the report says so.
8. **Hooks**: a call a project hook blocks is the worker's to follow or report; the main session
   never makes it itself, also in the fallback: the task is not handed off again, stays unmarked, is
   reported, and the next phase starts without it.
9. **Fallback**: no Agent tool, a worker's error (a usage limit included) or missing report, or a
   project that is not a git repository: "carry out the remaining tasks in this session" as core does
   (the bound of 6 is narrower: that phase's remaining items only, then the next phase goes to a worker), and say which and why in
   the completion report. The completion report always carries the line `Carried out in this session:
   none`, or the same prefix followed by the task ids and, for fix items, the phase and a short name; `tests/compose.sh` greps for it.
10. **Resume** (0.1.1): as spec Edge Cases, "A run resumes": the marks as committed at HEAD
    decide the phase; the baseline is the last `tasks: mark phase` commit, or HEAD; the worker gets
    the phase's commits and only its unmarked tasks; its own two fix hand-offs; uncommitted marks
    verified, never skipped; uncommitted changes to other files wait for the user.
11. **Narrowed, by name**: core's `For completed tasks, make sure to mark the task off as [X]`,
    `parallel tasks [P] can run together` and `Halt execution if any non-parallel task fails`.

## `tests/eval/run.sh <without|with|fallback> <out-dir>`

- Refuses: an unknown arm, an existing `<out-dir>` or one inside this checkout (its `CLAUDE.md`
  would load into the run), a checkout whose `git status --porcelain` is not
  empty (`.gitignore` keeps tool caches and the virtualenv out of it), a missing
  `claude`, `specify`, `uv`, `git`, `python3` or `jq`.
- Builds a scratch copy of `fixture/` as git tracks it, ignored files left out (it carries its
  `uv.lock` and `.specify/feature.json`),
  `git init`, `specify init --here --force --integration claude`, checks `.specify/feature.json`
  survived; for `with` and `fallback`, installs this checkout's `git archive` of HEAD served from
  localhost, with `SPECKIT_PYTHON_EXECUTABLE` set; checks the composed skill has the `## Story workers`
  section exactly when the arm installs the preset (else not counted, before the agent runs);
  commits.
- Every step after the refusals — `specify init`, the preset install, the setup commit, the agent,
  the suite and the held-out run — runs in the same clean environment, and each under its own
  deadline (3600 s for the agent, 600 s for each other step): `env -i` passing only `HOME`, `USER`, `LOGNAME`, `PATH`, `TMPDIR`,
  `LANG`, `TERM` and `SPECKIT_PYTHON_EXECUTABLE`, then setting only git's isolation (`GIT_CONFIG_GLOBAL=/dev/null`,
  `GIT_CONFIG_NOSYSTEM=1`, a fixed `eval` identity) — under a 3600-second deadline enforced by
  `tests/eval/bounded.py`, which runs the command in its own process group and kills the group (macOS
  ships no `timeout`): `claude -p "/speckit-implement" --model
  claude-opus-5-5 --effort medium --setting-sources project,local --strict-mcp-config --allowedTools
  "Agent Bash Edit Write Read Glob Grep TodoWrite" --output-format stream-json --verbose`, plus
  `--disallowedTools Agent` for `fallback`. The environment and git settings are written to
  `versions.txt`.
- Counts the arm only as research.md R6 "Counting" says; otherwise writes `status` (`not counted:
  <reason>`, a failed setup step included) with the reason,
  no `usage.txt` or `heldout.txt`, and exits 1. A refusal writes nothing and exits 2: it is fixed, not
  retried. Reruns are the caller's (quickstart).
- On a counted arm: runs the project's suite (`suite.txt`), then copies `heldout/` to
  `tests_heldout/` and runs it alone (`heldout.txt`: `passed <n>/<total>` from its junit report, then
  the output); writes `usage.txt` (`<model> <costUSD> cache_read <n> cache_creation <n>` per model, `sum <total>`, `five_hour <first>
  <last>`), `versions.txt` (this checkout's commit, tools, the main model ID and its effort, the `init` event's output
  style, plugin and MCP-server counts), `models.txt` (`model <id>` for every model in `modelUsage`,
  the main session's model and effort, and `agent <subagent_type> <model|-> <effort|-> <count>` for
  the main session's Agent calls), `commits.txt` (`git log --reverse --format='commit %H%n%s'
  --name-only <setup>..HEAD`: the commits after the setup commit, each a header, its subject and its
  files); `versions.txt` is `key: value` lines; `report.txt` is the completion report (the `result`
  event's text); `setup.log` and `claude.stderr` are kept for
  diagnosis; the scratch repository is kept in `<out-dir>/repo`
  and `status` = `ok`.

## `tests/eval/attribution.py <out-dir>`

Reads `stream.jsonl` and `commits.txt`, checks every clause of SC-003 and prints each with `ok` or
what failed: the main session's (no `parent_tool_use_id`) Write, Edit and NotebookEdit calls not on
the feature's `tasks.md`; a Sonnet entry in `modelUsage`; every main-session Agent call with
`model: "sonnet"` has `run_in_background: false`; each `## Phase` heading of the fixture's `tasks.md`
is the first line of at least one of their prompts; and none starts while another has no `tool_result`
yet (R1 17); the commits after the setup commit that
change more than `tasks.md` (at least one, each starting with `fixture:`); the `Carried out in this
session: none` line (list, quote, heading and emphasis marks and a closing stop aside); the phase
headings compared with heading and emphasis marks aside; no `permission_denials`. Then it lists the main session's Bash commands. Exit 0
when every clause holds, 1 when one does not, 2 when an input cannot be read or `status` is not
`ok`.

## `tests/eval/probes.sh`

Reruns R1 (1, 3, 4 with both `sonnet` and `opus`, 5, 7, 8, 9, 10, 11, 15, 17) headless and hermetic in
scratch repositories, prints the Claude Code version and one line per probe (`ok` or `FAIL` with what was seen), and exits 1 when any fails. Probe 5 and 8 compare
thinking tokens between a low and a high effort on the call, and fail when the high arm's is not
larger.
