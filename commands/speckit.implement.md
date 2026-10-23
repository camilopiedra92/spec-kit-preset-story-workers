## Story workers

In a project that is not a git repository, such as an export of one without its `.git`, **The call**
sends the run to **Fallback**: the remaining tasks are carried out in this session as core does, and
the completion report says which and why.

- This section narrows the steps above: where it and they differ, it applies.
- You are the main session. You hand each phase to a worker, verify it in your own runs, decide, and
  keep `tasks.md`.
- The workers write the code.

**Unit and order.**

- Hand each phase to a worker: one worker per phase of `tasks.md`.
- Take the phases in the order the steps above run them, the next only after the previous one's
  verification.
- Never run two workers at once.
- This narrows core's "parallel tasks [P] can run together": `[P]` tasks run inside their phase's
  worker, one after another.

**The call.**

- Start each worker with the Agent tool, `subagent_type: "general-purpose"`, `model: "sonnet"`,
  `effort: "medium"` and `run_in_background: false`.
- With no Agent tool, when the call returns an error, or when the project is not a git repository,
  go to **Fallback** below: core's own behaviour.

**The brief.**

- The brief opens with the phase's heading as `tasks.md` writes it.
- It carries the phase's unmarked tasks, or, for a fix, the finding.
- It says the phase's unmarked tasks may already be done, in whole or in part, and tells the worker
  to check each against the code and `git log`, and to complete only what is missing.
- It carries the feature directory.
- It carries the suite and static-check commands, from the project's instructions, else `plan.md`'s
  Technical Context.
- It carries the phases already marked.

It tells the worker:

- To follow core's "Load and analyze the implementation context", "Project Setup Verification"
  (Phase 1's worker only), "Execute implementation", "Implementation execution rules" and "Progress
  tracking and error handling" steps of `.claude/skills/speckit-implement/SKILL.md`, whose Story
  workers section is the main session's, not the worker's.
- That it commits each task in a commit of its own, staging only the files it changed, never
  `git add -A` or `-a`.
- That it commits what Project Setup Verification changes in a commit of its own.
- That it adds to the project's ignore file, in a commit of its own, any file the suite or the
  static checks generate that git does not ignore.
- That it never edits, stages, commits or reverts a file in the feature directory, and leaves a task
  that needs one unfinished, saying so.
- That it follows a call a project hook blocks, or leaves that task unfinished with the hook's
  message in its report.
- That it does not edit `tasks.md` (core's "mark the task off as [X]" in those steps is yours).
- That it does not start a review.
- That it does not start another worker.

**The report** the brief asks for:

- The first and last commit.
- The tasks done.
- The tasks found already done, with the commit or file that holds each.
- For each task not done, what stopped it.
- Anything found that no task covers.
- The output of its last whole-suite run.

**Verification.**

- Before a phase's first worker, record HEAD and run the static checks: that is the baseline.
- This narrows core's "For completed tasks, make sure to mark the task off as [X]": the main session
  marks a task [X] only after its own runs show the whole suite passing and no static-check finding
  the baseline lacked.
- It marks a task [X] only after its reading of the commits made since the recorded HEAD finds
  nothing the phase's tasks do not call for.
- It marks a task [X] only after `git status --porcelain --untracked-files=all`, run before its own
  suite and static-check runs, lists nothing outside the feature directory.
- What that `git status` lists is the worker's, and goes back to it as a finding.
- A task the worker found already done is marked on the suite, the static checks and its reading of
  the commit or file the worker cites.
- Run what the project names.
- Say in the completion report what the project does not name.
- A worker's report never marks a task.
- A review the phase calls for, and its fixes, resolve first.
- Then commit `tasks.md` with a message containing `tasks: mark phase <n>` (after any prefix the
  project's instructions require).
- Make no such commit when the phase marked nothing new.
- Only then start the next phase's worker.

**Hand-offs.**

- This narrows core's "Halt execution if any non-parallel task fails": every unfinished task, failed
  verification or review finding goes to a worker briefed with it, then verification again.
- The exception: an unfinished task that changes the feature directory, which this session carries
  out, as **A clean tree outside the feature** says.
- A review finding passes when a fresh review of it no longer reports it.
- A phase gets at most two fix hand-offs.
- Every hand-off after its first counts, whatever items it carries.
- When verification still fails after them (a fresh review still reporting its finding included),
  carry out the phase's remaining items in this session as core does.
- Tasks a worker reports finding join the current phase in `tasks.md`.
- Commit them with a message containing `tasks: add found tasks`.
- They go to the phase's next hand-off.
- Outside the items this session carries out, your only edits to tracked files are `tasks.md`
  (checkboxes, found tasks) and its commits.
- Running the suite, the static checks or core's extension hooks is not writing code.

**Reviews.**

- Start any review the user's or the project's instructions, or a command, call for in a fresh
  context: `subagent_type: "general-purpose"`, with `model` set to this session's model family (for
  example `opus`) and no `effort`.
- Never start a review in a worker.
- Where no fresh context can be started, the review does not run and the completion report says so.

**Hooks.**

- A call a project hook blocks is the worker's to follow or report.
- Never make such a call yourself, in the fallback too.
- Such a task is not handed off again.
- It stays unmarked and goes into the completion report.
- The next phase starts without it.
- Unless the suite is red because of it, in which case core's "Halt execution if any non-parallel
  task fails" applies and the run ends with the report.

**Fallback.**

- When no worker can carry on (no Agent tool, a worker's error, a usage limit included, a missing
  report, a project that is not a git repository, or uncommitted changes outside the feature
  directory when the run starts), carry out the remaining tasks in this session as core does.
- Say which and why in the completion report.
- The bound of two fix hand-offs is narrower: it moves only that phase's remaining items into this
  session, and the next phase goes to a worker as usual.
- The completion report always carries the line `Carried out in this session: none`, or
  `Carried out in this session:` followed by the task ids and, for fix items, the phase and a short
  name of each.

**Where a run starts.**

- `tasks.md`'s marks, `[X]` or `[x]`, read from the file as core reads it, are the record of what is
  done, whoever made them.
- Where a run starts is never read from commit messages.
- A run takes the phases in order and skips every phase whose tasks are all marked, wherever it
  falls.
- It starts at the first phase with an unmarked task, at Phase 1 when none is marked.
- When every task is marked, start no worker, commit nothing.
- Then say so in the completion report in place of the line below.
- Each phase's baseline is taken as Verification says.
- Work committed before the run is covered by the whole-suite run only.
- When a phase went to a worker, the completion report carries the line
  `Started at phase <n>: work committed before this run was covered by the whole suite, not read as a diff, its static-check findings in the baseline.`

**A clean tree outside the feature.**

- Before the first worker and before any of the run's own suite or static-check runs, run
  `git status --porcelain --untracked-files=all`.
- When it lists a path outside the feature directory, carry out the run in this session as core does
  (**Fallback**).
- In that case, name those paths in the completion report.
- Inside the feature directory, uncommitted changes stay as they are: the run neither asks about
  them nor stops for them.
- They are not a finding.
- No worker edits, stages, commits or reverts a file there.
- Commits that core's extension hooks make are core's, not the run's.
- The run's `tasks: mark phase` and `tasks: add found tasks` commits carry `tasks.md` as it stands,
  its earlier edits included.
- A task that changes a file in the feature directory is carried out in this session as core does,
  all of it.
- Its files in the feature directory are left uncommitted, as core leaves them.
- What this session changes outside the feature directory while carrying out items, it commits as
  soon as it has carried them out, before any later Verification or worker, in a commit whose
  message contains `tasks: carried out in this session`.
