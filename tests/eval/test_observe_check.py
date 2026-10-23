"""observe_check.py: E2's checks on a run's committed files, one check broken at a time."""

import json
from pathlib import Path
from typing import Any

import observe_check
import pytest

TASKS = (
    "# Tasks\n\n## Phase 1: One (Priority: P1)\n\n- [X] T001 a\n\n"
    "## Phase 2: Two (Priority: P2)\n\n- [X] T002 b\n"
)
PHASE_1 = "## Phase 1: One (Priority: P1)\n\nTasks T001."
PHASE_2 = "## Phase 2: Two (Priority: P2)\n\nTasks T002."
LOG = "git log --format='%h %s' abc123..HEAD"
COUNT = "git rev-list --count abc123..HEAD"
REPORT = "Done.\nCarried out in this session: none"


def agent(prompt: str) -> dict[str, Any]:
    call = {"type": "tool_use", "name": "Agent", "input": {"prompt": prompt}}
    return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [call]}}


def bash(command: str) -> dict[str, Any]:
    call = {"type": "tool_use", "name": "Bash", "input": {"command": command}}
    return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [call]}}


def write_run(root: Path, events: list[dict[str, Any]], **over: Any) -> Path:
    out = root / "run"
    (out / "repo/.specify").mkdir(parents=True)
    (out / "repo/.specify/feature.json").write_text('{"feature_directory": "specs/001-fx"}\n')
    (out / "repo/specs/001-fx").mkdir(parents=True)
    (out / "repo/specs/001-fx/tasks.md").write_text(TASKS)
    (out / "status").write_text(over.get("status", "ok\n"))
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (out / "report.txt").write_text(over.get("report", REPORT) + "\n")
    return out


def check(out: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = observe_check.main([str(out)])
    return code, capsys.readouterr().out


def test_a_range_read_after_each_worker_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events = [agent(PHASE_1), bash(LOG), agent(PHASE_2), bash(COUNT)]
    code, out = check(write_run(tmp_path, events), capsys)
    assert code == 0, out
    assert "ok range read after every worker (2)" in out
    assert "ok Carried out line present" in out


def test_a_worker_with_no_range_read_after_it_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The second worker is followed only by a read with no range.
    events = [agent(PHASE_1), bash(LOG), agent(PHASE_2), bash("git status --porcelain")]
    code, out = check(write_run(tmp_path, events), capsys)
    assert code == 1
    assert "FAIL range read after every worker: none after worker(s) [2]" in out


def test_a_range_read_before_the_worker_does_not_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events = [bash(LOG), agent(PHASE_1)]
    code, out = check(write_run(tmp_path, events), capsys)
    assert code == 1
    assert "FAIL range read after every worker" in out


def test_a_review_prompt_is_not_a_worker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events = [agent(PHASE_1), bash(LOG), agent("Review User Story 1."), bash("ls")]
    code, out = check(write_run(tmp_path, events), capsys)
    assert code == 0, out
    assert "(1)" in out


def test_a_report_without_the_carried_out_line_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(write_run(tmp_path, [agent(PHASE_1), bash(LOG)], report="Done."), capsys)
    assert code == 1
    assert "FAIL Carried out line present" in out


def test_cited_evidence_commands_are_counted_not_judged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    events = [
        agent(PHASE_1),
        bash(LOG),
        bash("git merge-base --is-ancestor abc HEAD"),
        bash("git ls-files --error-unmatch src/a.py"),
    ]
    code, out = check(write_run(tmp_path, events), capsys)
    assert code == 0
    assert "info cited-evidence commands (merge-base --is-ancestor, ls-files): 2" in out


def test_no_worker_or_an_uncounted_run_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert check(write_run(tmp_path, [bash(LOG)]), capsys)[0] == 2


def test_an_uncounted_run_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = write_run(tmp_path, [agent(PHASE_1)], status="not counted: exit 1\n")
    assert check(out, capsys)[0] == 2
