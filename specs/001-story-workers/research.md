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
  6. `--setting-sources project,local --strict-mcp-config`, with `CLAUDE_CODE_SUBAGENT_MODEL` and
     `CLAUDE_CODE_EFFORT_LEVEL` unset: the project's
     `CLAUDE.md` and skills loaded, for the main session and the subagent; the user's instructions,
     output style, skills, plugins and MCP servers did not; OAuth worked. Claude Code's built-in
     skills and plugins still loaded.
  7. `model: "opus"` on the call ran on `claude-opus-5-5`. A project `.claude/agents/general-purpose.md`
     with `model: haiku` replaced the built-in agent's prompt (its marker appeared in both replies),
     while the calls' `model` still decided the model (`claude-sonnet-5-5` usage for the `sonnet`
     call, none for `haiku`). The `result` event reported `is_error: false`, `subtype: success`.
  8. With a project `general-purpose` agent, the call's `effort` still applied: Sonnet's thinking on
     the counting problem was 0 at `"low"` and 398 at `"max"`.
  9. A project `PreToolUse` hook on `Write` exiting 2 blocked the subagent's write (no file), the
     subagent reported the hook's message verbatim, and the `result` event counted it in
     `permission_denials` (1).
  10. With `Stop` and `SubagentStop` hooks logging, two subagents and a final answer logged
      `substop substop stop`: the `Stop` hook fires once, at the end of the main session's turn.
  11. `--allowedTools Agent --disallowedTools Agent`: the main session reported no Agent tool, and
      `subagent_stats.spawned` was 0. The eval's tool list (`Agent Bash Edit Write Read Glob Grep
      TodoWrite`) let a Sonnet worker Write, Edit, run Bash and commit, with no permission denial.
  12. Hermetic flags (6) also exclude the user's hooks: the user's PreToolUse git guard, which blocks
      a `git reset --hard` that would lose work, did not run; the reset ran in the scratch repository.
      The user's settings are excluded too: the `init` event's `output_style` was `default`, while
      the user's settings set `Concise`.
  13. `--safe-mode` hid the project's `CLAUDE.md` and skills (the main session reported neither);
      `--bare` ended with `Not logged in` (`is_error: true`) under the owner's OAuth login.
  14. The stream carries `rate_limit_event`s with the subscription window's utilization
      (`five_hour.utilization`, two decimals) and the `result` event a `subagent_stats` block.
  15. A headless core `/speckit-implement` (no preset) on a one-task feature, hermetic, with git
      isolated (`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, an `eval` identity) and the
      eval's tool list: exit 0, one `result` event, `is_error: false`, no `permission_denials`, the
      task marked `[X]`, its test passing. Core wrote the code and an ignore file and committed
      nothing. The first attempt exited 127: macOS has no `timeout` command.
  16. `env -i` with only `HOME`, `USER`, `LOGNAME`, `PATH`, `TMPDIR`, `LANG` and `TERM`: the OAuth
      login still worked (`apiKeySource: none`, a normal reply), and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`,
      set in the calling shell, read as unset inside.
- **Not observed**: that `fable` is accepted as a `model` alias; the Agent tool's schema lists
  `sonnet`, `opus`, `haiku` and `fable`, and only the first three were run.
- **Alternatives considered**: *an agent definition in `.claude/agents/`*: works, but needs an
  installer, an upgrade path and a rule for owners' edits, and (7) shows a project's own definition
  would collide with it. *`CLAUDE_CODE_SUBAGENT_MODEL`*: a user setting a preset cannot set, and (4)
  it moves reviews too. *`/model` before implement*: one session, so the larger model's prompt
  cache is lost at each switch (prompt caches are per model in Anthropic's prompt-caching
  documentation; not observed here).

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

- **Decision**: the brief points at core's "Load and analyze the implementation context", "Project
  Setup Verification" (first phase), "Execute implementation", "Implementation execution rules" and
  "Progress tracking and error handling" steps; the worker commits each task and leaves `tasks.md`
  alone.
- **Rationale**: the composed skill is what the project installed, and R1 (3, 6) gives the worker the
  project's instructions, so nothing is copied. Core has no commit step; per-task commits give the
  main session a diff to read and a resumable state. Setup's ignore files are a write, so setup runs
  in the first worker too.
- **Alternatives considered**: *core's rules repeated in the brief*: a copy to keep in step with
  upstream; `tests/compose.sh` instead greps core for each step the brief names.

## R4. Verification before `[X]`

- **Decision**: the main session's own run of the suite and of the static checks (against a baseline
  taken before the phase's first worker), and its reading of the phase's diff. Narrows core's "For
  completed tasks, make sure to mark the task off as [X]"; `[P]` inside one worker narrows "parallel
  tasks [P] can run together"; failures going to a worker narrow "Halt execution if any non-parallel
  task fails".
- **Rationale**: a worker's report is its own account. R1 (10): a project's Stop hook fires at the
  end of the main session's turn, not at a subagent's, so only the main session's run catches a worker
  that returns red. The diff is read, not matched against paths named in tasks: deciding what a task
  "calls for" is judgement, which is what the larger model is kept for.
- **Alternatives considered**: *a mechanical scope check* (files a task names, lockfiles beside a
  manifest, ignore files): every rule added to it met a case it got wrong in review (checklist
  passes 1 and 2, 2026-10-13). *A `SubagentStop` hook*: something to install per project, for a check
  the main session already makes.

## R5. Fixes go to a worker; reviews name the main session's family

- **Decision**: every hand-off goes to a worker; a phase gets at most two fix hand-offs, after which
  its remaining items run as core does. A review that cannot get a fresh context does not run, and the
  report says so. A review is started with
  `subagent_type: "general-purpose"`, `model` set to the main session's family alias and no
  `effort`.
- **Rationale**: one rule keeps code writes in workers, which SC-003 checks, and the bound ends in
  core's behaviour rather than a stop (constitution IV). The Agent tool's schema takes family
  aliases, so the family is what can be named; R1 (4) shows a review without `model` would follow
  `CLAUDE_CODE_SUBAGENT_MODEL` (that `opus` on the call also wins over it is inferred from the
  `sonnet` case; the probes run both), and R1 (5) that without `effort` it thinks as hard as the session.
- **Alternatives considered**: *a bound per item* (two consecutive failing hand-offs on the same
  items): fixes that break each other alternate items and never reach it (checklist pass 3).
  *Stop and report at the bound or at a usage limit*: protects the larger
  model's budget, but a refusal where core would have finished breaks constitution IV; the owner
  chose core (Clarifications).

## R6. The eval

- **Fixture** `tests/eval/fixture/`: a small Python project (uv with a committed `uv.lock`, pytest,
  ruff) with a two-story feature: `specs/001-*/spec.md`, `plan.md` (its Technical Context names
  `uv run pytest` and `uv run ruff check`, and fixes the module and function names) and `tasks.md`,
  plus `.specify/feature.json` pointing at it; no `checklists/` directory, so core's checklist gate
  cannot stop a headless run. Its `CLAUDE.md` holds two rules: every commit message starts with
  `fixture:` (checked on the `with` arm's code commits: that is how instructions reaching the worker
  are seen), and each user story closes with a fresh review (so the measured usage includes the
  reviews the owner's own instructions ask for). `tests/eval/heldout/` holds at least one acceptance test per acceptance scenario
  of the fixture's spec.
- **Arms**: `without` (only `specify init`), `with` (this checkout's archive), `fallback` (`with`, run
  with `--disallowedTools Agent`, R1 (11)). They differ only in the preset and, for `fallback`, the
  tool.
- **Run** `tests/eval/run.sh <arm> <out-dir>`, hermetic per R1 (6, 12, 16): `env -i` with only
  `HOME`, `USER`, `LOGNAME`, `PATH`, `TMPDIR`, `LANG`, `TERM` and `SPECKIT_PYTHON_EXECUTABLE` (the
  specify CLI's own Python: preset installs need PyYAML, as dotfiles' `sdd-init.sh` and the sibling
  preset's `tests/compose.sh` record), git isolated as in R1 (15), then `claude -p "/speckit-implement" --model
  claude-opus-5-5 --effort medium --setting-sources project,local --strict-mcp-config --allowedTools
  "Agent Bash Edit Write Read Glob Grep TodoWrite" --output-format stream-json --verbose` (the same
  list in every arm), under a 3600-second deadline that `tests/eval/bounded.py` enforces by running
  the command in its own process group and killing the group (R1 (15): no `timeout` on macOS).
- **Counting** (FR-011): `claude` exited 0 within the deadline; the stream holds exactly one `result`
  event, with `is_error: false` and no `permission_denials`. Nothing else decides whether an arm
  counts: what the feature does — the commit rule, Sonnet usage, the `Carried out in this session`
  line, the reviews, the fallback's absence of Agent calls — is judged by SC-003, SC-005 and SC-007 on
  a counted run, so a rerun cannot hide a worker that misbehaved. A rerun forced by a `versions.txt`
  mismatch counts towards the two reruns. An arm that does not count is rerun, at most twice
  (Clarifications).
- **Alternatives considered for counting**: *the feature checks as counting rules* (the commit rule,
  Sonnet usage, no item carried out in the session): an arm that broke them would be rerun until it
  did not, hiding the failure (checklist pass 4); they are success criteria instead.
- **After a counted run**: the project's own suite runs first (`suite.txt`); then `heldout/` is copied
  to `tests_heldout/`, a directory the fixture does not use, and run alone (`heldout.txt`).
- **Outputs**: `status`, `stream.jsonl`, `usage.txt` (`costUSD` per model and the sum; the first and
  last `five_hour.utilization` beside them, R1 (14)), `heldout.txt`, `suite.txt`, `versions.txt`
  (date; Claude Code, Spec Kit, git, uv, Python, pytest, ruff; the main model ID and its effort; the
  environment allowlist and git isolation; the `init` event's output style, plugin and MCP-server
  counts, and built-in skills), `models.txt` (every model ID in `modelUsage` with its effort).
- **SC-003**: `tests/eval/attribution.py <out-dir>` lists the main session's (no
  `parent_tool_use_id`, R1 (1)) Write, Edit and NotebookEdit calls not on `tasks.md` (exit 1 if
  any), then its Bash commands.
- **Comparison**: every arm's `versions.txt` must match `without`'s but for the date; otherwise the
  comparison is refused and the arms are rerun. Worker models differ between arms by design and live
  in `models.txt`.
- **Probes** `tests/eval/probes.sh`: reruns R1 (1, 3, 4 with `sonnet` and `opus`, 5, 7, 8, 9, 10,
  11, 15) headless in scratch repositories, prints the Claude Code version, and checks each expected
  outcome (FR-012). R1 (6, 12) are not probed — a probe would have to write to the user's own
  configuration — and are checked on every eval run from its `init` event (output style, plugins,
  MCP servers); R1 (2) is covered by (9); R1 (14) is recorded, not relied on; R1 (16) is relied on by `run.sh` and a break shows as a
  failed run. For the probed observations, a Claude Code release that breaks one is
  a red probe, not a silent change in the eval.
- **Rationale**: per-model cost is the closest per-run observable to a subscription's usage, and
  summing every model is stricter than counting the larger one; the window's utilization moves with
  any other session on the account, so it is recorded, not judged. Held-out tests judge every arm by
  the same oracle (the SWE-bench approach). Hermetic, so the result is the preset's and
  reproducible.
- **Alternatives considered**: *the owner's configuration loaded*: measures one machine, not the
  preset. *`--bare`*: R1 (13), no OAuth. *`--safe-mode`*: R1 (13), no project `CLAUDE.md` or skills,
  so no Spec Kit. *A real feature replayed*: not rerunnable. *Three runs per arm*: the owner chose
  one, reported as directional.

## R7. The worker's effort is set; this is an exception

- **Decision**: `effort: "medium"` on the worker's call; nothing on the review's.
- **Rationale**: R1 (5): without it the worker inherits the main session's effort, so raising the
  session's effort to plan a hard feature would raise every worker's, the opposite of the feature's
  aim. Medium is Opus's default today (dotfiles `docs/claude-settings.md`, citing the model-config
  docs), so at default settings the eval measures what an unset value
  would. The owner's policy (dotfiles `docs/claude-settings.md`) leaves effort at each model's
  default because a written level freezes and nobody revisits it; here the eval reruns at every
  release that changes a rule (constitution III), records each model's effort in `versions.txt`,
  and the probes check that the call's effort still applies (R1 (5, 8)), which is the
  revisit the policy asks for. The review inherits: it should think as hard as the session chosen.
- **Alternatives considered**: *inherited*: no written level, but the coupling above. *`low`*: cheaper,
  unmeasured on a phase's work. This decision binds later features, so it moves to
  `docs/decisions/0001-worker-effort.md` before the PR opens.
