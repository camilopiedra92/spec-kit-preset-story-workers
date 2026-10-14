"""attribution.py: SC-003 from a `with` arm's outputs, each clause on its own."""

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ATTRIBUTION = Path(__file__).with_name("attribution.py")
FEATURE = "specs/001-greet"
PHASES = [
    "## Phase 1: Setup",
    "## Phase 2: User Story 1 - Greet",
    "## Phase 3: User Story 2 - Part",
]

Event = dict[str, Any]


def tool_use(id_: str, name: str, input_: dict[str, Any], parent: str | None = None) -> Event:
    return {
        "type": "assistant",
        "parent_tool_use_id": parent,
        "message": {"content": [{"type": "tool_use", "id": id_, "name": name, "input": input_}]},
    }


def tool_result(id_: str) -> Event:
    return {
        "type": "user",
        "parent_tool_use_id": None,
        "message": {"content": [{"type": "tool_result", "tool_use_id": id_, "content": "done"}]},
    }


def worker(id_: str, heading: str, **extra: Any) -> Event:
    call = {
        "subagent_type": "general-purpose",
        "model": "sonnet",
        "effort": "medium",
        "run_in_background": False,
        "prompt": f"{heading}\n\n- [ ] T001 do it\n",
    }
    call.update(extra)
    return tool_use(id_, "Agent", call)


def passing_stream(repo: Path) -> list[Event]:
    events: list[Event] = [{"type": "system", "subtype": "init", "model": "claude-opus-5-5"}]
    for n, heading in enumerate(PHASES):
        wid = f"w{n}"
        events += [
            worker(wid, heading),
            # A worker's own write: it has a parent, so it is not the main session's.
            tool_use(f"e{n}", "Write", {"file_path": str(repo / "src/greet.py")}, parent=wid),
            tool_result(wid),
            tool_use(f"m{n}", "Edit", {"file_path": str(repo / FEATURE / "tasks.md")}),
            tool_use(f"b{n}", "Bash", {"command": "uv run pytest"}),
        ]
    events.append(
        {
            "type": "result",
            "is_error": False,
            "result": "All phases done.\n\n**Carried out in this session:** none\n",
            "modelUsage": {
                "claude-opus-5-5": {"costUSD": 1.0},
                "claude-sonnet-5-5": {"costUSD": 0.5},
            },
            "permission_denials": [],
        }
    )
    return events


PASSING_COMMITS = """commit 1111
fixture: add the greet module

src/greet.py
commit 2222
fixture: tasks: mark phase 1

specs/001-greet/tasks.md
"""


def write_out(out: Path, events: list[Event], commits: str = PASSING_COMMITS) -> None:
    repo = out / "repo"
    (repo / ".specify").mkdir(parents=True)
    (repo / ".specify/feature.json").write_text(json.dumps({"feature_directory": FEATURE}))
    (repo / FEATURE).mkdir(parents=True)
    (repo / FEATURE / "tasks.md").write_text("# Tasks\n\n" + "\n\n".join(PHASES) + "\n")
    (out / "status").write_text("ok\n")
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (out / "commits.txt").write_text(commits)


def attribution(out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ATTRIBUTION), str(out)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_a_run_meeting_every_clause_exits_0_and_lists_the_bash_commands(tmp_path: Path) -> None:
    write_out(tmp_path, passing_stream(tmp_path / "repo"))
    result = attribution(tmp_path)
    assert result.returncode == 0, result.stdout
    assert "FAIL" not in result.stdout
    assert "uv run pytest" in result.stdout


def set_result(events: list[Event], **fields: Any) -> None:
    events[-1].update(fields)


def first_worker_input(events: list[Event]) -> dict[str, Any]:
    event = next(e for e in events if _is_worker(e))
    content: dict[str, Any] = event["message"]["content"][0]["input"]
    return content


def _is_worker(event: Event) -> bool:
    content = event.get("message", {}).get("content", [{}])[0]
    return bool(content.get("name") == "Agent" and content["input"].get("model") == "sonnet")


def main_session_write_outside_tasks(events: list[Event], repo: Path) -> None:
    events.insert(-1, tool_use("x", "Write", {"file_path": str(repo / "src/greet.py")}))


def no_sonnet_entry(events: list[Event], repo: Path) -> None:
    set_result(events, modelUsage={"claude-opus-5-5": {"costUSD": 1.0}})


def a_background_worker(events: list[Event], repo: Path) -> None:
    first_worker_input(events)["run_in_background"] = True


def a_phase_no_worker_opens(events: list[Event], repo: Path) -> None:
    # Three workers for phase 1 and none for phase 3: the count matches, the phases do not.
    for event in events:
        if _is_worker(event):
            event["message"]["content"][0]["input"]["prompt"] = PHASES[0] + "\n"


def a_heading_lower_in_the_prompt(events: list[Event], repo: Path) -> None:
    call = [e for e in events if _is_worker(e)][2]["message"]["content"][0]["input"]
    call["prompt"] = "Context first.\n" + PHASES[2] + "\n"


def overlapping_workers(events: list[Event], repo: Path) -> None:
    # The second worker starts before the first one's tool_result.
    first_result = next(i for i, e in enumerate(events) if e["type"] == "user")
    second_worker = [i for i, e in enumerate(events) if _is_worker(e)][1]
    events.insert(first_result, events.pop(second_worker))


def a_permission_denial(events: list[Event], repo: Path) -> None:
    set_result(events, permission_denials=[{"tool_name": "Bash"}])


def report_line_missing(events: list[Event], repo: Path) -> None:
    set_result(events, result="All phases done.")


def report_line_not_none(events: list[Event], repo: Path) -> None:
    set_result(events, result="Carried out in this session: T004")


Mutation = Callable[[list[Event], Path], None]


@pytest.mark.parametrize(
    "mutate",
    [
        main_session_write_outside_tasks,
        no_sonnet_entry,
        a_background_worker,
        a_phase_no_worker_opens,
        a_heading_lower_in_the_prompt,
        overlapping_workers,
        a_permission_denial,
        report_line_missing,
        report_line_not_none,
    ],
)
def test_each_stream_clause_fails_on_its_own(tmp_path: Path, mutate: Mutation) -> None:
    events = passing_stream(tmp_path / "repo")
    mutate(events, tmp_path / "repo")
    write_out(tmp_path, events)
    result = attribution(tmp_path)
    assert result.returncode == 1, result.stdout
    assert result.stdout.count("FAIL") == 1, result.stdout


@pytest.mark.parametrize(
    "commits",
    [
        # No commit changes more than tasks.md.
        "commit 2222\nfixture: tasks: mark phase 1\n\nspecs/001-greet/tasks.md\n",
        # A code commit without the fixture's prefix.
        "commit 1111\nadd the greet module\n\nsrc/greet.py\n",
    ],
)
def test_each_commit_clause_fails_on_its_own(tmp_path: Path, commits: str) -> None:
    write_out(tmp_path, passing_stream(tmp_path / "repo"), commits)
    result = attribution(tmp_path)
    assert result.returncode == 1, result.stdout
    assert result.stdout.count("FAIL") == 1, result.stdout


@pytest.mark.parametrize(
    "line",
    [
        "- **Carried out in this session:** none",
        "> Carried out in this session: `none`",
        "**Carried out in this session:** none.",
        "## Carried out in this session: none",
    ],
)
def test_the_report_line_holds_whatever_markup_wraps_it(tmp_path: Path, line: str) -> None:
    events = passing_stream(tmp_path / "repo")
    set_result(events, result=f"All phases done.\n\n{line}\n")
    write_out(tmp_path, events)
    result = attribution(tmp_path)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize(
    "first_line",
    [
        "Phase 2: User Story 1 - Greet",
        "**Phase 2: User Story 1 - Greet**",
        "### Phase 2: User Story 1 - Greet",
    ],
)
def test_a_phase_heading_counts_whatever_markup_wraps_it(tmp_path: Path, first_line: str) -> None:
    events = passing_stream(tmp_path / "repo")
    call = [e for e in events if _is_worker(e)][1]["message"]["content"][0]["input"]
    call["prompt"] = first_line + "\n\n- [ ] T002 do it\n"
    write_out(tmp_path, events)
    result = attribution(tmp_path)
    assert result.returncode == 0, result.stdout


def test_a_status_other_than_ok_exits_2(tmp_path: Path) -> None:
    write_out(tmp_path, passing_stream(tmp_path / "repo"))
    (tmp_path / "status").write_text("not counted: exit 1\n")
    assert attribution(tmp_path).returncode == 2


def test_an_unreadable_stream_exits_2(tmp_path: Path) -> None:
    write_out(tmp_path, passing_stream(tmp_path / "repo"))
    (tmp_path / "stream.jsonl").write_text("{not json\n")
    assert attribution(tmp_path).returncode == 2


def test_missing_commits_exit_2(tmp_path: Path) -> None:
    write_out(tmp_path, passing_stream(tmp_path / "repo"))
    (tmp_path / "commits.txt").unlink()
    assert attribution(tmp_path).returncode == 2
