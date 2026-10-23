"""nogit_check.py: E3's pass conditions on a run's committed files, one check broken at a time."""

import json
import subprocess
from pathlib import Path
from typing import Any

import nogit_check
import pytest

N = 4
TASKS = "# Tasks\n\n## Phase 1: One (Priority: P1)\n\n- [ ] T001 a\n- [ ] T002 b\n"
DONE = TASKS.replace("[ ]", "[X]")
REPORT = (
    "The project is not a git repository, so the run was carried out in this session as core "
    "does.\nCarried out in this session: T001, T002"
)


@pytest.fixture
def fixtures(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "fixtures/fx/heldout").mkdir(parents=True)
    (root / "fixtures/fx/heldout/N").write_text(f"{N}\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "fixture"], check=True)
    return root / "fixtures"


def agent(prompt: str) -> dict[str, Any]:
    call = {"type": "tool_use", "name": "Agent", "input": {"prompt": prompt}}
    return {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [call]}}


def write_run(fixtures: Path, root: Path, **over: Any) -> Path:
    out = root / "run"
    (out / "repo/.specify").mkdir(parents=True)
    (out / "repo/.specify/feature.json").write_text('{"feature_directory": "specs/001-fx"}\n')
    (out / "repo/specs/001-fx").mkdir(parents=True)
    (out / "repo/specs/001-fx/tasks.md").write_text(over.get("final", DONE))
    sha = subprocess.run(
        ["git", "-C", str(fixtures), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (out / "status").write_text(over.get("status", "ok\n"))
    (out / "versions.txt").write_text(
        f"commit: {sha}\nfixture: fx\nno_git: {over.get('no_git', 'yes')}\n"
    )
    events = over.get("events", [])
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (out / "heldout.txt").write_text(over.get("heldout", f"passed {N}/{N}\n"))
    (out / "report.txt").write_text(over.get("report", REPORT) + "\n")
    return out


def check(fixtures: Path, out: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = nogit_check.main([str(out)], fixtures=fixtures)
    return code, capsys.readouterr().out


def test_a_core_run_passes_every_check(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path), capsys)
    assert code == 0, out
    assert out.count("ok ") == 6


def test_a_worker_in_a_project_with_no_git_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = write_run(fixtures, tmp_path, events=[agent("## Phase 1: One (Priority: P1)\n\nGo.")])
    code, out = check(fixtures, run, capsys)
    assert code == 1
    assert "FAIL no worker started" in out


def test_a_review_prompt_is_not_a_worker(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = write_run(fixtures, tmp_path, events=[agent("Review the code of User Story 1.")])
    assert check(fixtures, run, capsys)[0] == 0


@pytest.mark.parametrize(
    ("report", "failing"),
    [
        ("Done.\nCarried out in this session: T001, T002", "report says why"),
        ("Not a git repository, so core's run.", "report carries the Carried out line"),
        (
            "Not a git repository.\nCarried out in this session: none",
            "report carries the Carried out line",
        ),
    ],
)
def test_a_report_missing_a_part_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], report: str, failing: str
) -> None:
    code, out = check(fixtures, write_run(fixtures, tmp_path, report=report), capsys)
    assert code == 1
    assert f"FAIL {failing}" in out


def test_an_unmarked_task_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = DONE.replace("[X] T002", "[ ] T002")
    code, out = check(fixtures, write_run(fixtures, tmp_path, final=final), capsys)
    assert code == 1
    assert "FAIL every task marked: T002" in out


def test_a_question_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ask = {
        "type": "assistant",
        "parent_tool_use_id": None,
        "message": {"content": [{"type": "tool_use", "name": "AskUserQuestion", "input": {}}]},
    }
    code, out = check(fixtures, write_run(fixtures, tmp_path, events=[ask]), capsys)
    assert code == 1
    assert "FAIL no question asked" in out


def test_a_held_out_score_below_n_fails(
    fixtures: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = check(
        fixtures, write_run(fixtures, tmp_path, heldout=f"passed {N - 1}/{N}\n"), capsys
    )
    assert code == 1
    assert "FAIL held-out N of N" in out


@pytest.mark.parametrize("over", [{"status": "not counted: exit 1\n"}, {"no_git": "no"}])
def test_a_run_that_does_not_count_or_kept_its_git_is_refused(
    fixtures: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    over: dict[str, Any],
) -> None:
    code, _ = check(fixtures, write_run(fixtures, tmp_path, **over), capsys)
    assert code == 2
