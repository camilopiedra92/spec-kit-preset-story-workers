"""resume_check.py: the resume eval's pass conditions, on a run's committed files.

Each test commits a three-phase fixture with a state that has Phase 1 done, then writes a run
directory that passes every check, and breaks one check at a time.
"""

import itertools
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import resume_check

N = 6
TASKS = """# Tasks

## Phase 1: User Story 1 - One (Priority: P1)

- [ ] T001 [US1] Write `tests/test_one.py` and the empty `conftest.py` in `tests/`
- [ ] T002 [US1] Implement `src/one.py` and `src/shared.py`

## Phase 2: User Story 2 - Two (Priority: P2)

- [ ] T003 [US2] Write `tests/test_two.py`
- [ ] T004 [US2] Implement `src/two.py` and `src/shared.py`
"""
DONE = TASKS.replace("- [ ] T001", "- [X] T001").replace("- [ ] T002", "- [x] T002")
PHASE_2 = "## Phase 2: User Story 2 - Two (Priority: P2)"
STATE = ["tests/test_one.py", "tests/conftest.py", "src/one.py", "src/shared.py"]
EDITED = "# Spec, edited and not committed\n"
PLAN = "# Plan\n"
DOC_TASK = "- [ ] T005 [US2] Record the design in `specs/001-fx/plan.md`\n"
ALL_MARKED = DONE.replace("- [ ] T003", "- [X] T003").replace("- [ ] T004", "- [X] T004")


@pytest.fixture
def fixtures(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    fx = root / "fixtures/fx"
    (fx / "project/specs/001-fx").mkdir(parents=True)
    (fx / "project/.specify").mkdir()
    (fx / "project/.specify/feature.json").write_text('{"feature_directory": "specs/001-fx"}\n')
    (fx / "project/specs/001-fx/tasks.md").write_text(TASKS)
    (fx / "heldout").mkdir()
    (fx / "heldout/N").write_text(f"{N}\n")
    committed = fx / "states/one-done/committed"
    (committed / "specs/001-fx").mkdir(parents=True)
    (committed / "specs/001-fx/tasks.md").write_text(DONE)
    # The state's files: what its finished phases left, whatever tasks.md calls them.
    for name in STATE:
        (committed / name).parent.mkdir(parents=True, exist_ok=True)
        (committed / name).write_text(f"# {name}\n")
    uncommitted = fx / "states/one-done/uncommitted/specs/001-fx"
    uncommitted.mkdir(parents=True)
    (uncommitted / "spec.md").write_text(EDITED)
    (fx / "project/specs/001-fx/plan.md").write_text(PLAN)
    # A state extending one-done: a task that changes the feature directory.
    doc = fx / "states/one-done-doc"
    (doc / "committed/specs/001-fx").mkdir(parents=True)
    (doc / "committed/specs/001-fx/tasks.md").write_text(DONE + DOC_TASK)
    (doc / "extends").write_text("one-done\n")
    # A state extending one-done: uncommitted work outside the feature directory.
    dirty = fx / "states/one-done-dirty"
    (dirty / "uncommitted").mkdir(parents=True)
    (dirty / "uncommitted/NOTES.md").write_text("notes\n")
    (dirty / "extends").write_text("one-done\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "fixture"], check=True)
    return root / "fixtures"


def commit_sha(fixtures: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(fixtures), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def worker(prompt: str) -> dict[str, Any]:
    call = {"type": "tool_use", "name": "Agent", "input": {"model": "sonnet", "prompt": prompt}}
    return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [call]}}


def write_run(fixtures: Path, root: Path, **over: Any) -> Path:
    out = root / "run"
    out.mkdir()
    (out / "status").write_text(over.get("status", "ok\n"))
    sha = commit_sha(fixtures)
    state = over.get("state", "one-done")
    (out / "versions.txt").write_text(f"commit: {sha}\nfixture: fx\nstate: {state}\narm: with\n")
    commits = over.get(
        "commits",
        "commit a1\nfixture: T003\ntests/test_two.py\n"
        "commit a2\nfixture: T004\nsrc/two.py\nsrc/shared.py\n",
    )
    (out / "commits.txt").write_text(commits)
    briefs = over.get("briefs", [f"{PHASE_2}\n\nTasks T003, T004."])
    events = [worker(b) for b in briefs] + over.get("extra_events", [])
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    repo = out / "repo"
    for name in STATE:
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(f"# {name}\n")
    for name, text in over.get("tree", {}).items():
        if text is None:
            (repo / name).unlink()
        else:
            (repo / name).write_text(text)
    final = repo / "specs/001-fx/tasks.md"
    final.parent.mkdir(parents=True, exist_ok=True)
    (repo / "specs/001-fx/spec.md").write_text(over.get("spec", EDITED))
    (repo / "specs/001-fx/plan.md").write_text(over.get("plan", PLAN))
    if state == "one-done-dirty":
        (repo / "NOTES.md").write_text(over.get("notes", "notes\n"))
    final.write_text(
        over.get(
            "final", DONE.replace("- [ ] T003", "- [X] T003").replace("- [ ] T004", "- [X] T004")
        )
    )
    (out / "heldout.txt").write_text(over.get("heldout", f"passed {N}/{N}\n"))
    report = (
        "Started at phase 2: work committed before this run was covered by the whole suite, "
        "not read as a diff, its static-check findings in the baseline."
    )
    (out / "report.txt").write_text(over.get("report", report) + "\n")
    return out


def check(fixtures: Path, out: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = resume_check.main([str(out)], fixtures=fixtures)
    return code, capsys.readouterr().out


def test_a_good_resume_passes_every_check(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path), capsys)
    assert code == 0, out
    assert out.count("ok ") == 9


def test_a_commit_touching_a_finished_only_file_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # src/shared.py is named by both phases, so only src/one.py and tests/test_one.py count.
    commits = "commit a1\nfixture: redo\nsrc/one.py\nsrc/shared.py\n"
    code, out = check(fixtures, write_run(fixtures, tmp_path, commits=commits), capsys)
    assert code == 1
    assert "FAIL finished phases untouched" in out and "src/one.py" in out
    assert "src/shared.py" not in out.split("FAIL finished phases untouched")[1].splitlines()[0]


def test_a_first_brief_for_another_phase_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    brief = "## Phase 1: User Story 1 - One (Priority: P1)\n\nRedo."
    code, out = check(fixtures, write_run(fixtures, tmp_path, briefs=[brief]), capsys)
    assert code == 1
    assert "FAIL first brief opens the first unfinished phase" in out


def test_a_held_out_score_below_n_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(
        fixtures, write_run(fixtures, tmp_path, heldout=f"passed {N - 1}/{N}\n"), capsys
    )
    assert code == 1
    assert "FAIL held-out N of N" in out


@pytest.mark.parametrize(
    "report",
    [
        "Carried out in this session: none",
        "Started at phase 1: covered by the suite.",
        "Started at phase 2: covered by the suite.",
        "Resumed at phase 2: covered by the suite.",
    ],
)
def test_a_report_without_the_right_resume_line_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], report: str
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path, report=report), capsys)
    assert code == 1
    assert "FAIL report names the start" in out


def test_a_run_that_did_not_count_is_refused(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = write_run(fixtures, tmp_path, status="not counted: exit 1\n")
    code, _ = check(fixtures, out, capsys)
    assert code == 2


def test_unreadable_input_is_refused(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = write_run(fixtures, tmp_path)
    (out / "commits.txt").unlink()
    code, _ = check(fixtures, out, capsys)
    assert code == 2


def test_a_commit_touching_a_state_file_its_tasks_name_loosely_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # T001 names conftest.py only as `conftest.py` in `tests/`: the state, not the
    # backticked paths, says which files the finished phases left.
    commits = "commit a1\nfixture: redo\ntests/conftest.py\n"
    code, out = check(fixtures, write_run(fixtures, tmp_path, commits=commits), capsys)
    assert code == 1
    assert "FAIL finished phases untouched: tests/conftest.py" in out


def test_a_later_brief_for_a_finished_phase_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    briefs = [f"{PHASE_2}\n\nTasks T003, T004.", "## Phase 1: User Story 1 - One (Priority: P1)\n"]
    code, out = check(fixtures, write_run(fixtures, tmp_path, briefs=briefs), capsys)
    assert code == 1
    assert "FAIL no brief opens a finished phase" in out


def test_a_run_with_no_worker_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path, briefs=[]), capsys)
    assert code == 1
    assert "FAIL first brief opens the first unfinished phase: '(no worker)'" in out


def test_a_task_left_unmarked_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = DONE.replace("- [ ] T003", "- [X] T003")
    code, out = check(fixtures, write_run(fixtures, tmp_path, final=final), capsys)
    assert code == 1
    assert "FAIL every task marked: T004" in out


def test_a_question_in_the_stream_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ask = {"type": "tool_use", "name": "AskUserQuestion", "input": {}}
    event = {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [ask]}}
    code, out = check(fixtures, write_run(fixtures, tmp_path, extra_events=[event]), capsys)
    assert code == 1
    assert "FAIL no question asked" in out


@pytest.mark.parametrize("text", ["# rewritten\n", None])
def test_a_finished_file_changed_in_the_tree_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str | None
) -> None:
    # Left uncommitted, or deleted: no commit names it, the tree still shows it.
    run = write_run(fixtures, tmp_path, tree={"tests/test_one.py": text})
    code, out = check(fixtures, run, capsys)
    assert code == 1
    assert "FAIL finished phases untouched: tests/test_one.py" in out


def test_an_uncommitted_change_altered_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path, spec="# Spec\n"), capsys)
    assert code == 1
    assert "FAIL uncommitted changes untouched: specs/001-fx/spec.md" in out


def test_an_uncommitted_change_committed_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    commits = "commit a1\nfixture: T003\ntests/test_two.py\nspecs/001-fx/spec.md\n"
    code, out = check(fixtures, write_run(fixtures, tmp_path, commits=commits), capsys)
    assert code == 1
    assert "FAIL uncommitted changes untouched: specs/001-fx/spec.md" in out


# A task that changes the feature directory: the main session's, never committed.

DOC_FINAL = ALL_MARKED + DOC_TASK.replace("- [ ]", "- [X]")
DOC_REPORT = (
    "Started at phase 2: work committed before this run was covered by the whole suite, "
    "not read as a diff, its static-check findings in the baseline.\n"
    "Carried out in this session: T005"
)


def doc_run(fixtures: Path, root: Path, **over: Any) -> Path:
    args: dict[str, Any] = {
        "state": "one-done-doc",
        "final": DOC_FINAL,
        "plan": "# Plan\n\n## As built\n",
        "report": DOC_REPORT,
    }
    return write_run(fixtures, root, **{**args, **over})


def test_a_feature_directory_task_carried_out_in_this_session_passes(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, doc_run(fixtures, tmp_path), capsys)
    assert code == 0, out
    assert "ok feature-directory tasks carried out in this session: T005" in out


@pytest.mark.parametrize(
    "over",
    [
        {"plan": PLAN},
        {"commits": "commit a1\nfixture: T005\nspecs/001-fx/plan.md\n"},
        {"report": DOC_REPORT.replace("T005", "none")},
    ],
    ids=["unchanged", "committed", "not-in-carried-out"],
)
def test_a_feature_directory_task_not_carried_out_so_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], over: dict[str, Any]
) -> None:
    code, out = check(fixtures, doc_run(fixtures, tmp_path, **over), capsys)
    assert code == 1
    assert "FAIL feature-directory tasks carried out in this session: T005" in out


# Uncommitted work outside the feature directory: the whole run is core's.

DIRTY_REPORT = (
    "NOTES.md is uncommitted outside the feature directory, so the run was carried out as core does.\n"
    "Carried out in this session: T003, T004"
)


def dirty_run(fixtures: Path, root: Path, **over: Any) -> Path:
    args: dict[str, Any] = {"state": "one-done-dirty", "briefs": [], "report": DIRTY_REPORT}
    return write_run(fixtures, root, **{**args, **over})


def test_a_run_sent_to_core_passes(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, dirty_run(fixtures, tmp_path), capsys)
    assert code == 0, out
    assert "ok no worker started: core's run" in out
    assert "ok report names the paths outside the feature directory" in out


def test_a_worker_on_a_dirty_tree_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = dirty_run(fixtures, tmp_path, briefs=[f"{PHASE_2}\n\nTasks T003, T004."])
    code, out = check(fixtures, run, capsys)
    assert code == 1
    assert "FAIL no worker started" in out


@pytest.mark.parametrize(
    "over", [{"report": "Carried out in this session: T003, T004"}, {"notes": "changed\n"}]
)
def test_a_dirty_path_unnamed_or_touched_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], over: dict[str, Any]
) -> None:
    code, out = check(fixtures, dirty_run(fixtures, tmp_path, **over), capsys)
    assert code == 1
    assert "NOTES.md" in out


# A worker is any main-session Agent call briefed with a phase, whatever its model.


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", None])
def test_a_worker_on_any_model_counts(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], model: str | None
) -> None:
    event = worker(f"{PHASE_2}\n\nTasks T003, T004.")
    call = event["message"]["content"][0]
    if model is None:
        del call["input"]["model"]
    else:
        call["input"]["model"] = model
    code, out = check(fixtures, dirty_run(fixtures, tmp_path, extra_events=[event]), capsys)
    assert code == 1
    assert "FAIL no worker started" in out


def test_a_review_call_is_not_a_worker(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    review = worker("You are a fresh reviewer. Do not edit files.")
    review["message"]["content"][0]["input"]["model"] = "opus"
    code, out = check(fixtures, dirty_run(fixtures, tmp_path, extra_events=[review]), capsys)
    assert code == 0, out


def test_a_task_line_deleted_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = "\n".join(line for line in ALL_MARKED.splitlines() if "T004" not in line) + "\n"
    code, out = check(fixtures, write_run(fixtures, tmp_path, final=final), capsys)
    assert code == 1
    assert "FAIL every task marked: T004" in out


def test_a_circular_state_chain_is_refused(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = fixtures.parent
    for name, base in [("loop-a", "loop-b"), ("loop-b", "loop-a")]:
        (fixtures / "fx/states" / name).mkdir(parents=True)
        (fixtures / "fx/states" / name / "extends").write_text(base + "\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "loop"], check=True)
    code = resume_check.main(
        [str(write_run(fixtures, tmp_path, state="loop-a"))], fixtures=fixtures
    )
    assert code == 2
    assert "more than 5 deep" in capsys.readouterr().err


def test_a_state_chain_deeper_than_five_is_refused(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # deep-0 extends deep-1 ... deep-5 extends one-done: seven layers.
    names = [f"deep-{n}" for n in range(6)] + ["one-done"]
    for name, base in itertools.pairwise(names):
        (fixtures / "fx/states" / name).mkdir(parents=True)
        (fixtures / "fx/states" / name / "extends").write_text(base + "\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(fixtures.parent)]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "deep"], check=True)
    code = resume_check.main(
        [str(write_run(fixtures, tmp_path, state="deep-0"))], fixtures=fixtures
    )
    assert code == 2
    assert "more than 5 deep" in capsys.readouterr().err
