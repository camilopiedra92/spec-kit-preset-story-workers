## Story workers

This section narrows the steps above: where it and they differ, it applies. You are the main
session. You hand each phase to a worker, verify it in your own runs, decide, and keep `tasks.md`;
the workers write the code.

**Unit and order.** Hand each phase to a worker: one worker per phase of `tasks.md`, in the order
the steps above run the phases, the next only after the previous one's verification, never two at
once. This narrows core's "parallel tasks [P] can run together": `[P]` tasks run inside their
phase's worker, one after another, since two workers would write the same worktree and index.

**The call.** Start each worker with the Agent tool, `subagent_type: "general-purpose"`,
`model: "sonnet"`, `effort: "medium"` and `run_in_background: false`, so its report is in hand
before you verify. With no Agent tool, when the call returns an error, or when the project is not a
git repository (the commits, diffs and baseline below need git), go to **Fallback** below: core's
own behaviour.

**The brief.** It opens with the phase's heading as `tasks.md` writes it, then carries: the phase's
unmarked tasks, which may already be done, in whole or in part (check each against the code and `git
log`, and complete only what is missing), or, for a fix, the finding; the feature directory; the
suite and static-check commands, from the project's instructions, else `plan.md`'s Technical
Context; and the phases already marked. It tells the worker to follow core's "Load and analyze the
implementation context", "Project Setup Verification" (Phase 1's worker only), "Execute
implementation", "Implementation execution rules" and "Progress tracking and error handling" steps
of `.claude/skills/speckit-implement/SKILL.md`, whose Story workers section is the main session's,
not the worker's; that the worker commits each task in a commit of its own, staging only the files
it changed, never `git add -A` or `-a`; that it commits what Project Setup Verification changes in a
commit of its own, and adds to the project's ignore file, in a commit of its own, any file the suite
or the static checks generate that git does not ignore; that it never edits, stages, commits or
reverts a file in the feature directory, and leaves a task that needs one unfinished, saying so;
that it follows a call a project hook blocks, or leaves that task unfinished with the hook's message
in its report; and that it does not edit `tasks.md` (core's "mark the task off as [X]" in those
steps is yours), start a review or start another worker.

**The report** the brief asks for: the first and last commit; the tasks done; the tasks found
already done, with the commit or file that holds each; for each task not done, what stopped it;
anything found that no task covers; the output of its last whole-suite run.

**Verification.** Before a phase's first worker, record HEAD and run the static checks: that is the
baseline. This narrows core's "For completed tasks, make sure to mark the task off as [X]": the main
session marks a task [X] only after its own runs show the whole suite passing and no static-check
finding the baseline lacked, its reading of the commits made since the recorded HEAD finds nothing
the phase's tasks do not call for, and `git status --porcelain --untracked-files=all`, run before
its own suite and static-check runs, lists nothing outside the feature directory (what it lists is
the worker's, and goes back to it as a finding); a task the worker found already done is marked on
the suite, the static checks and its reading of the commit or file the worker cites. Run what the
project names; say in the completion report what it does not name. A worker's report never marks a
task. A review the phase calls for, and its fixes, resolve first; then commit `tasks.md` with a
message containing `tasks: mark phase <n>` (after any prefix the project's instructions require;
none when the phase marked nothing new), and only then start the next phase's worker.

**Hand-offs.** This narrows core's "Halt execution if any non-parallel task fails": every unfinished
task (except one that changes the feature directory, which this session carries out, as **A clean
tree outside the feature** says), failed verification or review finding goes to a worker briefed
with it, then verification again; a review finding passes when a fresh review of it no longer
reports it. A phase gets at most two fix hand-offs, every hand-off after its first counting,
whatever items it carries; when verification still fails after them (a fresh review still reporting
its finding included), carry out the phase's remaining items in this session as core does. Tasks a
worker reports finding join the current phase in `tasks.md`, committed with a message containing
`tasks: add found tasks`, and go to its next hand-off. Outside the items this session carries out,
your only edits to tracked files are `tasks.md` (checkboxes, found tasks) and its commits; running
the suite, the static checks or core's extension hooks is not writing code.

**Reviews.** Start any review the user's or the project's instructions, or a command, call for in a
fresh context: `subagent_type: "general-purpose"`, with `model` set to this session's model family
(for example `opus`) and no `effort`, so it thinks as hard as this session. Never in a
worker. Where no fresh context can be started, the review does not run and the completion report
says so: a review by the context that wrote the code is not one.

**Hooks.** A call a project hook blocks is the worker's to follow or report; never make it yourself,
in the fallback too. Such a task is not handed off again: it stays unmarked, goes into the
completion report, and the next phase starts without it, unless the suite is red because of it, in
which case core's "Halt execution if any non-parallel task fails" applies and the run ends with the
report.

**Fallback.** When no worker can carry on (no Agent tool, a worker's error, a usage limit included,
a missing report, a project that is not a git repository, or uncommitted changes outside the feature
directory when the run starts), carry out the remaining tasks in this session as core does, and say
which and why in the completion report. The bound of two fix hand-offs is narrower: it moves only
that phase's remaining items into this session, and the next phase goes to a worker as usual. The
completion report always carries the line `Carried out in this session: none`, or `Carried out in
this session:` followed by the task ids and, for fix items, the phase and a short name of each.

**Where a run starts.** `tasks.md`'s marks, `[X]` or `[x]`, read from the file as core reads it, are
the record of what is done, whoever made them; where a run starts is never read from commit
messages. A run takes the phases in order and skips every phase whose tasks are all marked, wherever
it falls; it starts at the first phase with an unmarked task, at Phase 1 when none is marked. When
every task is marked, start no worker, commit nothing, and say so in the completion report in place
of the line below. Each phase's baseline is taken as Verification says. Work committed before the
run is covered by the whole-suite run only. When a phase went to a worker, the completion report
carries the line `Started at phase <n>: work committed before this run was covered by the whole
suite, not read as a diff, its static-check findings in the baseline.`

**A clean tree outside the feature.** Before the first worker and before any of the run's own suite
or static-check runs, run `git status --porcelain --untracked-files=all`. When it lists a path
outside the feature directory, a worker's changes could not be kept apart from that work: carry out
the run in this session as core does (**Fallback**), and name those paths in the completion report.
Inside the feature directory, uncommitted changes stay as they are: the run neither asks about them
nor stops for them, they are not a finding, and no worker edits, stages, commits or reverts a file
there. Commits that core's extension hooks make are core's, not the run's. The run's `tasks: mark
phase` and `tasks: add found tasks` commits carry `tasks.md` as it stands, its earlier edits
included. A task that changes a file in the feature directory is carried out in this session as core
does, all of it, and its files in the feature directory are left uncommitted, as core leaves them.
What this session changes outside the feature directory while carrying out items, it commits as soon
as it has carried them out, before any later Verification or worker, in a commit whose message
contains `tasks: carried out in this session`.
