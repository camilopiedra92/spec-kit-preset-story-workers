# Research: Story workers

Observations are dated and name the versions they ran on (constitution III).

## R1. The worker is a model and an effort on the call

- **Decision**: hand each phase to the `general-purpose` agent with `model: "sonnet"` and
  `effort: "medium"` on the Agent call. Nothing is installed in the project.
- **Observed** 2026-10-13, Claude Code 2.1.296, git 2.56.0, macOS; `claude -p --output-format
  stream-json --verbose` in scratch repositories; one run each:
  1. `general-purpose` with `model: "sonnet"`: the subagent's turns ran on `claude-sonnet-5-5`, the
     main session's on `claude-opus-5-5`. The subagent's tool calls appear in the stream with
     `parent_tool_use_id` set; the main session's have none. The `result` event's `modelUsage` had a
     `claude-sonnet-5-5` entry with its own `costUSD`: subagents are counted there.
  2. A project `PostToolUse` hook saw the subagent's calls with `agent_id` set; a hook exiting 2 had
     its stderr quoted verbatim by the subagent.
  3. With a marker line in the project's `CLAUDE.md`, the subagent, told to use no tools, quoted it
     and the first line of the user's global instructions.
  4. With `CLAUDE_CODE_SUBAGENT_MODEL=haiku`: a call with `model: "sonnet"` ran on Sonnet, one without
     `model` on `claude-haiku-5-5`; without the variable, a call without `model` ran on the main
     session's model.
  5. Effort, on a counting problem the subagent solved without tools (Sonnet's thinking tokens):
     main `--effort low`, no effort on the call: 174; main `max`, none: 516; main `medium`, call
     `effort: "low"`: 161; main `medium`, call `"max"`: 1081. The subagent inherits the main
     session's effort, and the call's `effort` wins. On an easier problem all four arms were within
     316–353, while the main session's own thinking moved from 49 (low) to 395 (high).
  6. `--setting-sources project,local --strict-mcp-config`, with the variables unset: the project's
     `CLAUDE.md` and skills loaded, for the main session and the subagent; the user's instructions,
     output style, skills, plugins and MCP servers did not; OAuth worked. Claude Code's built-in
     skills and plugins still loaded.
  7. `model: "opus"` on the call ran on `claude-opus-5-5`. A project `.claude/agents/general-purpose.md`
     with `model: haiku` replaced the built-in agent's prompt (its marker appeared in both replies),
     while the calls' `model` still decided the model (`claude-sonnet-5-5` usage for the `sonnet`
     call, none for `haiku`). The `result` event reported `is_error: false`, `subtype: success`.
- **Alternatives considered**: *an agent definition in `.claude/agents/`*: works, but needs an
  installer, an upgrade path and a rule for owners' edits, and (7) shows a project's own definition
  would collide with it. *`CLAUDE_CODE_SUBAGENT_MODEL`*: a user setting a preset cannot set, and (4)
  it moves reviews too. *`/model` before implement*: one session, so the larger model's prompt
  cache is lost at each switch.

## R2. One worker per phase, in order, in this worktree

- **Decision**: one worker per phase of `tasks.md`, the next only after the previous one's
  verification; `[P]` tasks run inside their phase's worker.
- **Rationale**: core executes phase by phase and verifies each phase before the next; tasks within
  a phase build on each other, which a worker per task would rediscover. Two workers at once would
  write the same worktree and index.
- **Alternatives considered**: *a worker per task*: least context per worker, most verification on
  the larger model. *Parallel workers in worktrees*: a merge per phase, an environment per worktree;
  the gain is wall-clock, not usage.

## R3. The brief points at core; the worker commits

- **Decision**: the brief points at core's "Project Setup Verification" (first phase), "Execute
  implementation", "Implementation execution rules" and "Progress tracking and error handling"
  steps, and the worker commits one commit per task and leaves `tasks.md` alone.
- **Rationale**: the composed skill is what the project installed, and R1 (3, 6) gives the worker the
  project's instructions, so nothing is copied. Core has no commit step; per-task commits give the
  main session the range FR-004 checks and a resumable state. Setup's ignore files are a write; in a
  worker, the main session's writes stay `tasks.md` only.
- **Alternatives considered**: *core's rules repeated in the brief*: a copy to keep in step with
  upstream; `tests/compose.sh` instead greps core for each step the brief names.

## R4. Verification before `[X]`

- **Decision**: FR-004: the suite, the static checks against a baseline taken before the phase, and
  the phase's commit range against the files its tasks name. Narrows core's "For completed tasks,
  make sure to mark the task off as [X]"; `[P]` inside one worker narrows "parallel tasks [P] can run
  together".
- **Rationale**: a worker's report is its own account. A project's Stop hook fires at the end of the
  main session's turn, not a subagent's, so only the main session's run catches a worker that
  returns red.
- **Alternatives considered**: *a `SubagentStop` hook*: something to install per project, for a check
  the main session already makes.

## R5. Fixes go to a worker; reviews name the main session's family

- **Decision**: every hand-off goes to a worker, bounded by the no-progress rule (FR-006). A review is
  started with `model` set to the main session's family alias and no `effort`.
- **Rationale**: one rule keeps every code write in a worker, which SC-003 checks. The Agent tool's
  `model` takes family aliases (`sonnet`, `opus`, `haiku`, `fable`), so the family is what can be
  named; R1 (4) shows a review without `model` would follow `CLAUDE_CODE_SUBAGENT_MODEL`, and R1 (5)
  that without `effort` it thinks as hard as the session the owner chose.

## R6. The eval

- **Fixture** `tests/eval/fixture/`: a small Python project (uv, pytest, ruff) with a two-story
  feature whose `spec.md`, `plan.md` (which fixes the module and function names) and `tasks.md` are
  written; no `checklists/` directory, so core's checklist gate cannot stop a headless run. Its
  `CLAUDE.md` holds one rule — every commit message starts with `fixture:` — whose effect `run.sh`
  checks on the `with` arm's worker commits: that is how instructions reaching the worker are seen.
  `tests/eval/heldout/` holds at least one acceptance test per acceptance scenario of the fixture's
  spec, copied into a run only after it has ended.
- **Arms**: `without` (only `specify init`), `with` (this checkout's archive), `fallback` (`with`, run
  with `--disallowedTools Agent`). They differ only in the preset and, for `fallback`, the tool.
- **Run** `tests/eval/run.sh <arm> <out-dir>`, hermetic per R1 (6): `env -u CLAUDE_CODE_SUBAGENT_MODEL
  -u CLAUDE_CODE_EFFORT_LEVEL claude -p "/speckit-implement" --model claude-opus-5-5 --effort medium
  --setting-sources project,local --strict-mcp-config --allowedTools "Agent Bash Edit Write Read Glob
  Grep TodoWrite" --output-format stream-json --verbose` (the same list in every arm), under a
  deadline that kills its process group.
- **Counting** (FR-011): an arm counts only when `claude` exited 0 within the deadline and the
  `result` event has `is_error: false`; the stream must hold exactly one `result`. The `with` arm also
  fails unless `modelUsage` has a Sonnet entry and every worker commit message starts with `fixture:`;
  `fallback` fails if `modelUsage` has any model but the main one.
- **Outputs**: `status` (`ok` or the reason), `stream.jsonl`, `usage.txt` (`costUSD` per model and
  the sum), `heldout.txt`, `suite.txt`, `versions.txt` (date; Claude Code, Spec Kit, git, uv,
  Python, pytest; the model IDs in `modelUsage`; the built-in skills and plugins in the stream's
  `init` event).
- **SC-003**: `tests/eval/attribution.py <out-dir>` lists the main session's (no
  `parent_tool_use_id`) Write, Edit and NotebookEdit calls not on `tasks.md` (exit 1 if any), then
  its Bash commands.
- **Rationale**: per-model cost is the closest observable to a subscription's usage, and summing
  every model is stricter than counting the larger one. Held-out tests judge every arm by the same
  oracle (the SWE-bench approach). Hermetic, so the result is the preset's and reproducible; the
  owner's own setup (a review per story in their global instructions) would add usage to both arms
  and blur the difference.
- **Alternatives considered**: *the owner's configuration loaded*: measures one machine, not the
  preset. *`--bare`*: no OAuth and no project `CLAUDE.md`. *`--safe-mode`*: disables the project's
  `CLAUDE.md` and skills, so Spec Kit itself. *A real feature replayed*: not rerunnable. *Three runs
  per arm*: the owner chose one, reported as directional.

## R7. The worker's effort is set; this is an exception

- **Decision**: `effort: "medium"` on the worker's call; nothing on the review's.
- **Rationale**: R1 (5): without it the worker inherits the main session's effort, so raising the
  session's effort to plan a hard feature would raise every worker's, the opposite of the feature's
  aim. Medium is Opus's default today, so at default settings the eval measures what an unset value
  would. The owner's policy (dotfiles `docs/claude-settings.md`) leaves effort at each model's
  default because a written level freezes and nobody revisits it; here the eval reruns at every
  release that changes a rule (constitution III) and records each model's effort, which is the
  revisit the policy asks for. The review inherits: it should think as hard as the session chosen.
- **Alternatives considered**: *inherited*: no written level, but the coupling above. *`low`*: cheaper,
  unmeasured on a phase's work. This decision binds later features, so it moves to
  `docs/decisions/0001-worker-effort.md` before the PR opens.
