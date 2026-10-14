# Research: Story workers

Observations are dated and name the versions they ran on (constitution III).

## R1. The worker is a model on the call

- **Decision**: hand a phase to the built-in `general-purpose` agent with `model: "sonnet"` on the
  Agent call. Nothing is installed in the project.
- **Observed** 2026-10-13, Claude Code 2.1.296, git 2.56.0, `claude -p --output-format stream-json`
  in scratch repositories, one run each:
  1. `general-purpose` with `model: "sonnet"`: the subagent's turns ran on `claude-sonnet-5-5`, the
     main session's on `claude-opus-5-5`.
  2. A project `PostToolUse` hook saw the subagent's calls with `agent_id` set; a hook exiting 2
     had its stderr quoted verbatim by the subagent.
  3. With a marker line in the project's `CLAUDE.md`, the subagent, told to use no tools, quoted the
     marker and the first line of the user's global instructions; its only tool call was its
     hand-back.
  4. With `CLAUDE_CODE_SUBAGENT_MODEL=haiku`: a call with `model: "sonnet"` ran on Sonnet, a call
     without `model` on `claude-haiku-5-5`; without the variable, a call without `model` ran on the
     main session's model.
- **Consequences**: (3) the worker follows the project's own instructions with no copy in the brief;
  (4) the reviewer's call names the main session's model too (R5).
- **Alternatives considered**: *an agent definition in `.claude/agents/`*: works, but needs an
  installer, an upgrade path and a rule for owners' edits, to restrict tools a phase needs anyway.
  *`CLAUDE_CODE_SUBAGENT_MODEL`*: a user setting a preset cannot set, and it would move reviews too.
  *`/model` before implement*: one session, so the larger model's prompt cache is lost at each
  switch, and reviews would need a switch back.

## R2. One worker per phase, in order, in this worktree

- **Decision**: one worker per phase of `tasks.md`, the next only after the previous one's
  verification; `[P]` tasks run inside their phase's worker, one after another.
- **Rationale**: core already executes phase by phase and verifies each phase before the next; a
  user story's tasks build on each other, which a worker per task would rediscover from the code.
  Two workers at once would write the same worktree and the same index.
- **Alternatives considered**: *a worker per task*: least context per worker, most verification on
  the larger model, most re-reading. *Parallel workers in worktrees*: a merge step for every phase,
  and each worktree needs its own environment; the gain is wall-clock, not usage.

## R3. The brief points at core, it does not copy it

- **Decision**: the brief tells the worker to follow the "Execute implementation", "Implementation
  execution rules" and "Progress tracking and error handling" steps of
  `.claude/skills/speckit-implement/SKILL.md` for its tasks, and gives it the phase's tasks, the
  feature directory, the project's suite and static-check commands, and what earlier workers
  finished.
- **Rationale**: the composed skill is what this project installed; the worker reads the rules the
  main session reads, and R1 (3) gives it the project's instructions.
- **Alternatives considered**: *core's rules repeated in the brief*: a copy the composition test
  would have to keep in step with upstream.

## R4. Verification before `[X]`

- **Decision**: the main session marks a task `[X]` only after its own runs (spec FR-004). This
  narrows core's "For completed tasks, make sure to mark the task off as [X]"; `[P]` inside one
  worker narrows "parallel tasks [P] can run together". `tests/compose.sh` greps core for both.
- **Rationale**: a worker's report is the agent's own account of its work. A project's Stop hook
  fires at the end of the main session's turn, not at a subagent's stop, so only the main session's
  run catches a worker that returns red.
- **Alternatives considered**: *a `SubagentStop` hook*: something to install in each project, for a
  check the main session's run already makes before anything is marked.

## R5. Fixes go to a worker; reviews name the main session's model

- **Decision**: every fix goes to a worker briefed with it (owner, Clarifications 2026-10-13). Any
  review the project or a command calls for is started with `model` set to the main session's own
  model, in a fresh context.
- **Rationale**: one rule keeps every code write in a worker, which SC-003 checks; R1 (4) shows a
  review without `model` follows `CLAUDE_CODE_SUBAGENT_MODEL` when set.
- **Alternatives considered**: *fixes in the main session*: fewer hand-offs, writes on the larger
  model.

## R6. The eval

- **Decision**:
  - **Fixture** `tests/eval/fixture/`: a small Python project (uv, pytest) with a two-story feature
    whose `spec.md`, `plan.md` and `tasks.md` are written, so both arms start from the same tasks and
    only implement differs; `tests/eval/heldout/` holds acceptance tests written from the fixture's
    spec, never copied into a run until it has ended.
  - **Arms**: `with` installs this checkout's archive; `without` installs nothing beyond `specify
    init`. They differ only in the preset.
  - **Run** `tests/eval/run.sh <with|without> <out-dir>`: a scratch copy, `specify init`, the arm's
    preset, a commit, then `claude -p "/speckit-implement" --model claude-opus-5-5 --output-format
    stream-json --verbose` with the tools implement needs allowed, under a deadline that kills its
    process group; then the held-out tests run against the result.
  - **Usage**: the sum of `modelUsage[*].costUSD` in the stream's one `result` event (observed in R1
    to include subagents); the run fails unless there is exactly one.
  - **Outputs**: `stream.jsonl`, `usage.txt`, `heldout.txt`, `suite.txt`, `versions.txt`.
  - **SC-003**: `tests/eval/attribution.py <out-dir>` reads the stream and lists the main session's
    Write, Edit and NotebookEdit calls not on `tasks.md` (exit 1 if any) and its Bash commands.
- **Rationale**: the subscription's window is not exposed per run; the per-model cost Claude Code
  reports is the closest observable, and summing every model is stricter than counting the larger
  one. Held-out tests judge both arms by the same oracle, independent of the tests each arm wrote
  (the SWE-bench approach); the agent's own tests differ between arms and cannot be compared.
- **Alternatives considered**: *a real feature replayed*: more representative, not rerunnable.
  *Three runs per arm*: the owner chose one, reported as directional. *Mutation score of each arm's
  tests*: measures the tests, not the delivered behaviour, and needs a mutation tool in the fixture.
