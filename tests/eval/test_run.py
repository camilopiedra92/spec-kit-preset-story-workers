"""run.sh: its refusals and its counting, against stub claude, specify and uv.

Each test copies run.sh and bounded.py into a throwaway git checkout with a
minimal fixture, so a refusal about the checkout's state is tested on a
checkout the test controls. The stubs read what to do from files beside
them: run.sh's clean environment drops every variable a test could set.
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

HERE = Path(__file__).parent
BASH = shutil.which("bash") or "/bin/bash"
REQUIRED = ["claude", "specify", "uv", "git", "python3", "jq"]
STORIES = 2
OUTPUTS = [
    "status",
    "stream.jsonl",
    "usage.txt",
    "heldout.txt",
    "suite.txt",
    "versions.txt",
    "models.txt",
    "commits.txt",
    "report.txt",
]

CLAUDE = r"""#!/bin/sh
here=$(dirname "$0")
[ "$1" = --version ] && { echo "2.1.299 (Claude Code)"; exit 0; }
printf '%s\n' "$@" > "$here/claude.args"
# A worker's commit, so commits.txt has something after the setup commit.
git commit -q --allow-empty -m "fixture: work"
cat "$here/stream.jsonl"
exit "$(cat "$here/claude.exit")"
"""

SPECIFY = r"""#!/bin/sh
here=$(dirname "$0")
case "$1" in
  init) mkdir -p .specify .claude/skills/speckit-implement
        echo core > .claude/skills/speckit-implement/SKILL.md ;;
  preset) echo "$@" >> "$here/specify.preset"
          [ -e "$here/specify.nocompose" ] ||
            echo "## Story workers" >> .claude/skills/speckit-implement/SKILL.md ;;
  version) echo "specify 1.1.3" ;;
esac
"""

UV = r"""#!/bin/sh
here=$(dirname "$0")
[ "$1" = --version ] && { echo "uv 0.13.0"; exit 0; }
[ "$1 $2" = "tool dir" ] && { echo "$here/tools"; exit 0; }
shift  # run
case "$*" in
  *--version*) echo "$1 9.9.9"; exit 0 ;;
  *--junitxml=*)
    for a in "$@"; do case "$a" in --junitxml=*) xml=${a#--junitxml=} ;; esac; done
    echo '<testsuites><testsuite tests="4" failures="1" errors="0" skipped="0"/></testsuites>' > "$xml"
    echo "3 passed, 1 failed"; exit 1 ;;
  *) echo "5 passed"; exit 0 ;;
esac
"""


def init_event(**fields: Any) -> dict[str, Any]:
    event = {
        "type": "system",
        "subtype": "init",
        "model": "claude-opus-5-5",
        "output_style": "default",
        "mcp_servers": [],
        "plugins": [{"name": "cc-plugin-agents-md", "path": "builtin"}],
        "skills": ["speckit-implement"],
    }
    event.update(fields)
    return event


def agent_call(id_: str, subagent_type: str, **input_: Any) -> dict[str, Any]:
    return {
        "type": "assistant",
        "parent_tool_use_id": None,
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": id_,
                    "name": "Agent",
                    "input": {"subagent_type": subagent_type, "prompt": "p", **input_},
                }
            ]
        },
    }


def agent_result(id_: str, is_error: bool = False) -> dict[str, Any]:
    block = {"type": "tool_result", "tool_use_id": id_, "content": "done", "is_error": is_error}
    return {"type": "user", "parent_tool_use_id": None, "message": {"content": [block]}}


def result_event(**fields: Any) -> dict[str, Any]:
    event = {
        "type": "result",
        "is_error": False,
        "result": "Carried out in this session: none",
        "modelUsage": {
            "claude-opus-5-5": {
                "costUSD": 1.25,
                "cacheReadInputTokens": 100,
                "cacheCreationInputTokens": 20,
            },
            "claude-sonnet-5-5": {"costUSD": 0.5},
        },
        "permission_denials": [],
    }
    event.update(fields)
    return event


def rate_limit(utilization: float) -> dict[str, Any]:
    window = {"five_hour": {"utilization": utilization}}
    return {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": window}}


def stream(*, init: dict[str, Any] | None = None, results: int = 1, **result: Any) -> list[Any]:
    reviews = [
        event
        for n in range(STORIES)
        for event in (agent_call(f"r{n}", "general-purpose"), agent_result(f"r{n}"))
    ]
    return [
        init or init_event(),
        rate_limit(0.5),
        *reviews,
        rate_limit(0.52),
        *[result_event(**result) for _ in range(results)],
    ]


def executable(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    eval_dir = root / "tests/eval"
    eval_dir.mkdir(parents=True)
    for name in ("run.sh", "bounded.py"):
        shutil.copy2(HERE / name, eval_dir / name)
    fixture = eval_dir / "fixture"
    feature = fixture / "specs/001-greet"
    feature.mkdir(parents=True)
    (fixture / ".specify").mkdir()
    (fixture / ".specify/feature.json").write_text('{"feature_directory": "specs/001-greet"}\n')
    stories = "".join(f"### User Story {n + 1} - S{n + 1}\n\n" for n in range(STORIES))
    (feature / "spec.md").write_text("# Spec\n\n" + stories)
    (feature / "tasks.md").write_text("# Tasks\n\n## Phase 1: Setup\n")
    (eval_dir / "heldout").mkdir()
    (eval_dir / "heldout/test_greet.py").write_text("def test_x() -> None:\n    pass\n")
    (root / ".gitignore").write_text("ignored.txt\n")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "checkout"], check=True)
    return root


@pytest.fixture
def stubs(tmp_path: Path) -> Path:
    bin_ = tmp_path / "stubs"
    bin_.mkdir()
    executable(bin_ / "claude", CLAUDE)
    executable(bin_ / "specify", SPECIFY)
    executable(bin_ / "uv", UV)
    (bin_ / "tools/specify-cli/bin").mkdir(parents=True)
    os.symlink(shutil.which("python3") or "python3", bin_ / "tools/specify-cli/bin/python")
    script(bin_, stream())
    return bin_


def script(stubs: Path, events: list[Any], exit_: int = 0) -> None:
    (stubs / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (stubs / "claude.exit").write_text(f"{exit_}\n")


def run(
    checkout: Path, stubs: Path, arm: str, out: Path, path: str | None = None
) -> subprocess.CompletedProcess[str]:
    env = {"HOME": os.environ["HOME"], "PATH": path or f"{stubs}:{os.environ['PATH']}"}
    return subprocess.run(
        [BASH, str(checkout / "tests/eval/run.sh"), arm, str(out)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


# Refusals: exit 2, nothing written.


def test_an_unknown_arm_is_refused(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    result = run(checkout, stubs, "sideways", tmp_path / "out")
    assert result.returncode == 2
    assert not (tmp_path / "out").exists()


def test_an_existing_out_dir_is_refused_and_left_alone(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("x")
    assert run(checkout, stubs, "with", out).returncode == 2
    assert [p.name for p in out.iterdir()] == ["keep"]


@pytest.mark.parametrize("change", ["tracked", "untracked"])
def test_a_checkout_with_changes_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path, change: str
) -> None:
    if change == "tracked":
        (checkout / ".gitignore").write_text("changed\n")
    else:
        (checkout / "stray.txt").write_text("x")
    assert run(checkout, stubs, "with", tmp_path / "out").returncode == 2
    assert not (tmp_path / "out").exists()


def test_an_out_dir_inside_the_checkout_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    # Its ancestors' CLAUDE.md would load into the run.
    out = checkout / "runs/out"
    assert run(checkout, stubs, "with", out).returncode == 2
    assert not out.exists()


def test_an_out_dir_reached_through_a_symlink_into_the_checkout_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    (tmp_path / "link").symlink_to(checkout)
    out = tmp_path / "link/runs/out"
    assert run(checkout, stubs, "with", out).returncode == 2
    assert not out.exists()


def test_a_dotdot_out_dir_leading_outside_the_checkout_is_accepted(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    out = checkout / "../out"
    assert run(checkout, stubs, "with", out).returncode == 0
    assert (tmp_path / "out/status").read_text() == "ok\n"


def test_an_ignored_file_is_not_a_change(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    (checkout / "ignored.txt").write_text("x")
    assert run(checkout, stubs, "with", tmp_path / "out").returncode == 0


@pytest.mark.parametrize("missing", REQUIRED)
def test_a_missing_tool_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path, missing: str
) -> None:
    # PATH holds the required tools but one; the refusal comes before run.sh
    # needs anything but bash builtins.
    tools = tmp_path / "tools-path"
    tools.mkdir()
    for name in REQUIRED:
        found = shutil.which(name, path=f"{stubs}:{os.environ['PATH']}")
        if name != missing and found:
            os.symlink(found, tools / name)
    result = run(checkout, stubs, "with", tmp_path / "out", path=str(tools))
    assert result.returncode == 2
    assert missing in result.stderr
    assert not (tmp_path / "out").exists()


# Counting: status with the reason, no usage.txt or heldout.txt, exit 1.


def test_an_errored_review_is_not_a_review(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    events = stream()
    events[3] = agent_result("r0", is_error=True)
    script(stubs, events)
    out = tmp_path / "out"
    assert run(checkout, stubs, "without", out).returncode == 1
    assert "reviews: 1 of 2" in (out / "status").read_text()


def test_a_review_without_subagent_type_is_general_purpose(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    # The Agent tool's default type is general-purpose.
    events = stream()
    del events[2]["message"]["content"][0]["input"]["subagent_type"]
    script(stubs, events)
    assert run(checkout, stubs, "without", tmp_path / "out").returncode == 0


def test_a_preset_that_did_not_compose_does_not_count(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    (stubs / "specify.nocompose").write_text("")
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 1
    assert "preset not composed" in (out / "status").read_text()
    assert not (stubs / "claude.args").exists()


def test_files_git_ignores_stay_out_of_the_fixture_copy(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    (checkout / "tests/eval/fixture/ignored.txt").write_text("stray")
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 0
    assert not (out / "repo/ignored.txt").exists()


NOT_COUNTED = [
    ("exit 1", "with", stream(), 1),
    ("deadline", "with", stream(), 124),
    ("result events: 0", "with", stream(results=0), 0),
    ("result events: 2", "with", stream(results=2), 0),
    ("is_error", "with", stream(is_error=True), 0),
    ("permission denial", "without", stream(permission_denials=[{"tool_name": "Bash"}]), 0),
    ("permission denial", "fallback", stream(permission_denials=[{"tool_name": "Bash"}]), 0),
    ("output style", "with", stream(init=init_event(output_style="Concise")), 0),
    (
        "plugin",
        "with",
        stream(init=init_event(plugins=[{"name": "mine", "path": "/Users/x/plugins/mine"}])),
        0,
    ),
    ("mcp server", "with", stream(init=init_event(mcp_servers=[{"name": "ynab"}])), 0),
]


@pytest.mark.parametrize(("reason", "arm", "events", "exit_"), NOT_COUNTED)
def test_a_run_that_does_not_count(
    checkout: Path,
    stubs: Path,
    tmp_path: Path,
    reason: str,
    arm: str,
    events: list[Any],
    exit_: int,
) -> None:
    script(stubs, events, exit_)
    out = tmp_path / "out"
    result = run(checkout, stubs, arm, out)
    assert result.returncode == 1, result.stdout + result.stderr
    status = (out / "status").read_text()
    assert status.startswith("not counted"), status
    assert reason in status
    assert not (out / "usage.txt").exists()
    assert not (out / "heldout.txt").exists()


def test_without_needs_a_general_purpose_review_per_story(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    # One review and one Explore call: two Agent calls, one review, two stories.
    events = stream()
    events[2] = agent_call("x", "Explore")
    script(stubs, events)
    out = tmp_path / "out"
    assert run(checkout, stubs, "without", out).returncode == 1
    assert "reviews: 1 of 2" in (out / "status").read_text()


def test_a_permission_denial_in_with_still_counts(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    # In `with`, a denial is the feature's failure, judged by SC-003, not a reason to rerun.
    script(stubs, stream(permission_denials=[{"tool_name": "Bash"}]))
    assert run(checkout, stubs, "with", tmp_path / "out").returncode == 0


# A counted run.


@pytest.mark.parametrize("arm", ["without", "with", "fallback"])
def test_a_counted_run_writes_every_output(
    checkout: Path, stubs: Path, tmp_path: Path, arm: str
) -> None:
    out = tmp_path / "out"
    result = run(checkout, stubs, arm, out)
    assert result.returncode == 0, result.stdout + result.stderr
    for name in OUTPUTS:
        assert (out / name).is_file(), name
    assert (out / "status").read_text() == "ok\n"
    assert (out / "repo/.git").is_dir()
    assert (out / "repo/tests_heldout/test_greet.py").is_file()

    assert (out / "heldout.txt").read_text().startswith("passed 3/4\n")
    usage = (out / "usage.txt").read_text()
    assert "claude-opus-5-5 1.25" in usage
    assert "sum 1.75" in usage
    assert "five_hour 0.5 0.52" in usage
    assert "claude-opus-5-5 1.25 cache_read 100 cache_creation 20" in usage
    assert (out / "report.txt").read_text() == "Carried out in this session: none\n"

    commits = (out / "commits.txt").read_text()
    assert "fixture: work" in commits
    assert "fixture: setup" not in commits

    versions = (out / "versions.txt").read_text()
    for key in ("date", "commit", "claude", "specify", "git", "uv", "python", "pytest", "ruff"):
        assert f"\n{key}: " in f"\n{versions}", key
    assert "main_model: claude-opus-5-5" in versions
    assert "main_effort: medium" in versions
    assert "output_style: default" in versions

    models = (out / "models.txt").read_text()
    assert "model claude-sonnet-5-5" in models
    assert "agent general-purpose - - 2" in models

    args = (stubs / "claude.args").read_text().splitlines()
    assert ("--disallowedTools" in args) == (arm == "fallback")
    assert "--setting-sources" in args and "--strict-mcp-config" in args
    installed = (stubs / "specify.preset").exists()
    assert installed == (arm != "without")
