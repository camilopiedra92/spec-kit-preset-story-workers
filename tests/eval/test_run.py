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
    "usage.json",
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
echo "${DISABLE_AUTOUPDATER-unset}" > "$here/claude.autoupdater"
# What versions.txt holds when the agent starts (the cwd is <out>/repo).
cp ../versions.txt "$here/versions.seen" 2> /dev/null || : > "$here/versions.seen"
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

# usage.py's stand-in: run.sh's clean environment drops variables, so it reads
# its exit code from a file beside it and writes what the real one would.
USAGE = """import sys
from pathlib import Path

here = Path(__file__).parent
out = Path(sys.argv[-1])
code = int((here / "usage.exit").read_text()) if (here / "usage.exit").exists() else 0
if code == 0:
    (out / "usage.txt").write_text("reconciled yes\\n")
    (out / "usage.json").write_text("{}\\n")
elif code == 3:
    # Python's own exit 1: an exception before main() could run.
    print("Traceback (most recent call last):\\nTypeError: unsupported operand")
    code = 1
else:
    print("unreconciled: no transcript" if code == 1 else "Traceback: bug")
(here / "usage.args").write_text(" ".join(sys.argv[1:]))
sys.exit(code)
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
        "session_id": "sess-1",
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
    (eval_dir / "usage.py").write_text(USAGE)
    fixture = eval_dir / "fixtures/greet/project"
    feature = fixture / "specs/001-greet"
    feature.mkdir(parents=True)
    (fixture / ".specify").mkdir()
    (fixture / ".specify/feature.json").write_text('{"feature_directory": "specs/001-greet"}\n')
    stories = "".join(f"### User Story {n + 1} - S{n + 1}\n\n" for n in range(STORIES))
    (feature / "spec.md").write_text("# Spec\n\n" + stories)
    (feature / "tasks.md").write_text("# Tasks\n\n## Phase 1: Setup\n")
    heldout = eval_dir / "fixtures/greet/heldout"
    heldout.mkdir()
    (heldout / "test_greet.py").write_text("def test_x() -> None:\n    pass\n")
    (root / ".gitignore").write_text("ignored.txt\nusage.exit\nusage.args\n")
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
    # Claude Code's transcripts for session sess-1, where run.sh looks for them.
    project = bin_ / "home/.claude/projects/-tmp-some-repo"
    (project / "sess-1/subagents").mkdir(parents=True)
    (project / "sess-1.jsonl").write_text('{"type": "assistant"}\n')
    (project / "sess-1/subagents/agent-a1.jsonl").write_text('{"type": "assistant"}\n')
    (project / "sess-1/subagents/agent-a1.meta.json").write_text('{"agentType": "Explore"}\n')
    return bin_


def script(stubs: Path, events: list[Any], exit_: int = 0) -> None:
    (stubs / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    (stubs / "claude.exit").write_text(f"{exit_}\n")


def run(
    checkout: Path,
    stubs: Path,
    arm: str,
    out: Path,
    path: str | None = None,
    fixture: str = "greet",
    baseline: Path | None = None,
    home: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        "HOME": str(home or stubs / "home"),
        "PATH": path or f"{stubs}:{os.environ['PATH']}",
    }
    args = ["--baseline", str(baseline)] if baseline else []
    return subprocess.run(
        [BASH, str(checkout / "tests/eval/run.sh"), *args, fixture, arm, str(out)],
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


@pytest.mark.parametrize("fixture", ["nowhere", "../fixtures/greet", ""])
def test_an_unknown_fixture_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path, fixture: str
) -> None:
    result = run(checkout, stubs, "with", tmp_path / "out", fixture=fixture)
    assert result.returncode == 2
    assert "fixture" in result.stderr
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("part", ["project", "heldout"])
def test_a_fixture_lacking_a_part_is_refused(
    checkout: Path, stubs: Path, tmp_path: Path, part: str
) -> None:
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(checkout)]
    subprocess.run([*git, "rm", "-rq", f"tests/eval/fixtures/greet/{part}"], check=True)
    subprocess.run([*git, "commit", "-qm", f"drop {part}"], check=True)
    result = run(checkout, stubs, "with", tmp_path / "out")
    assert result.returncode == 2
    assert part in result.stderr
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
    (checkout / "tests/eval/fixtures/greet/project/ignored.txt").write_text("stray")
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
    # usage.txt is usage.py's, not a jq summary of modelUsage.
    assert (out / "usage.txt").read_text() == "reconciled yes\n"
    assert (checkout / "tests/eval/usage.args").read_text() == str(out.resolve())
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
    assert "fixture: greet" in versions
    assert f"arm: {arm}" in versions

    models = (out / "models.txt").read_text()
    assert "model claude-sonnet-5-5" in models
    assert "agent general-purpose - - 2" in models

    args = (stubs / "claude.args").read_text().splitlines()
    assert ("--disallowedTools" in args) == (arm == "fallback")
    assert "--setting-sources" in args and "--strict-mcp-config" in args
    installed = (stubs / "specify.preset").exists()
    assert installed == (arm != "without")


# 002: the auto-updater, versions before the agent, the baseline, transcripts, usage.py.


def test_the_auto_updater_is_disabled_for_the_agent(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    assert run(checkout, stubs, "with", tmp_path / "out").returncode == 0
    assert (stubs / "claude.autoupdater").read_text() == "1\n"


PRE_RUN = [
    "commit",
    "claude",
    "specify",
    "git",
    "uv",
    "main_model",
    "main_effort",
    "environment",
    "git_isolation",
    "fixture",
    "arm",
    "autoupdater",
]
POST_RUN = ["python", "pytest", "ruff", "output_style", "plugins", "mcp_servers", "skills", "date"]


def keys(text: str) -> set[str]:
    return {line.split(":", 1)[0] for line in text.splitlines() if ":" in line}


def test_pre_run_keys_exist_before_the_agent_and_post_run_keys_after(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 0
    seen = keys((stubs / "versions.seen").read_text())
    assert set(PRE_RUN) <= seen
    assert not seen & set(POST_RUN)
    assert set(PRE_RUN + POST_RUN) <= keys((out / "versions.txt").read_text())
    assert "autoupdater: disabled" in (out / "versions.txt").read_text()


def baseline_run(checkout: Path, stubs: Path, tmp_path: Path) -> Path:
    base = tmp_path / "without-1-1"
    assert run(checkout, stubs, "without", base).returncode == 0
    return base


def test_a_baseline_differing_only_in_arm_proceeds(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    base = baseline_run(checkout, stubs, tmp_path)
    out = tmp_path / "with-1-1"
    result = run(checkout, stubs, "with", out, baseline=base)
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_baseline_differing_in_a_pre_run_key_refuses_before_the_agent(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    base = baseline_run(checkout, stubs, tmp_path)
    versions = base / "versions.txt"
    versions.write_text(versions.read_text().replace("claude: 2.1.299", "claude: 2.1.300"))
    (stubs / "claude.args").unlink()
    out = tmp_path / "with-1-1"
    result = run(checkout, stubs, "with", out, baseline=base)
    assert result.returncode == 2
    assert not (stubs / "claude.args").exists()
    status = (out / "status").read_text()
    assert status.startswith("refused") and "claude" in status


def test_a_baseline_differing_in_an_init_key_does_not_count(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    base = baseline_run(checkout, stubs, tmp_path)
    versions = base / "versions.txt"
    versions.write_text(versions.read_text().replace("skills: speckit-implement", "skills: other"))
    out = tmp_path / "with-1-1"
    result = run(checkout, stubs, "with", out, baseline=base)
    assert result.returncode == 1
    status = (out / "status").read_text()
    assert status.startswith("not counted") and "skills" in status
    assert not (out / "heldout.txt").exists()


def test_a_missing_baseline_is_refused(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    result = run(checkout, stubs, "with", tmp_path / "out", baseline=tmp_path / "nowhere")
    assert result.returncode == 2
    assert "baseline" in result.stderr
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("exit_", [0, 124])
def test_transcripts_are_copied_whenever_the_stream_names_a_session(
    checkout: Path, stubs: Path, tmp_path: Path, exit_: int
) -> None:
    events = stream() if exit_ == 0 else stream(results=0)
    script(stubs, events, exit_)
    out = tmp_path / "out"
    run(checkout, stubs, "with", out)
    assert (out / "transcripts/sess-1.jsonl").is_file()
    assert (out / "transcripts/subagents/agent-a1.jsonl").is_file()
    assert (out / "transcripts/subagents/agent-a1.meta.json").is_file()


def test_unreconciled_usage_does_not_count(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    (checkout / "tests/eval/usage.exit").write_text("1\n")
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 1
    status = (out / "status").read_text()
    assert status.startswith("not counted: unreconciled: no transcript"), status
    for name in ("usage.txt", "usage.json", "suite.txt", "heldout.txt"):
        assert not (out / name).exists(), name


def test_a_usage_fault_is_a_harness_fault(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    (checkout / "tests/eval/usage.exit").write_text("2\n")
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 2
    assert (out / "status").read_text().startswith("refused: harness fault")
    assert not (out / "heldout.txt").exists()


PROBES_CLAUDE = r"""#!/bin/sh
echo "${DISABLE_AUTOUPDATER-unset}" >> "$(dirname "$0")/probes.autoupdater"
[ "$1" = --version ] && { echo "2.1.299 (Claude Code)"; exit 0; }
exit 1
"""


def test_the_probes_disable_the_auto_updater(tmp_path: Path) -> None:
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    executable(bin_ / "claude", PROBES_CLAUDE)
    env = {"HOME": str(tmp_path), "PATH": f"{bin_}:{os.environ['PATH']}"}
    result = subprocess.run(
        [BASH, str(HERE / "probes.sh"), str(tmp_path / "probes")],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    seen = (bin_ / "probes.autoupdater").read_text().split()
    assert seen and set(seen) == {"1"}, seen
    # The closing summary runs.sh and compare.py require, counting the lines above it.
    out = result.stdout.splitlines()
    summary = [line for line in out if line.startswith("probes: ")]
    oks = sum(line.startswith("ok ") for line in out)
    fails = sum(line.startswith("FAIL ") for line in out)
    assert summary == [f"probes: {oks} ok, {fails} FAIL"] and fails > 0, result.stdout


def test_an_exit_1_that_is_not_unreconciled_is_a_harness_fault(
    checkout: Path, stubs: Path, tmp_path: Path
) -> None:
    (checkout / "tests/eval/usage.exit").write_text("3\n")
    out = tmp_path / "out"
    assert run(checkout, stubs, "with", out).returncode == 2
    assert (out / "status").read_text().startswith("refused: harness fault: TypeError")
    assert "Traceback (most recent call last)" in (out / "usage.log").read_text()


def test_a_run_through_the_real_usage_py(checkout: Path, stubs: Path, tmp_path: Path) -> None:
    shutil.copy2(HERE / "usage.py", checkout / "tests/eval/usage.py")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(checkout)]
    subprocess.run([*git, "commit", "-qam", "real usage.py"], check=True)
    u = {
        "input_tokens": 1000,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
    entry = {"type": "assistant", "message": {"id": "m1", "model": "claude-opus-5-5", "usage": u}}
    project = stubs / "home/.claude/projects/-tmp-some-repo"
    (project / "sess-1.jsonl").write_text(json.dumps(entry) + "\n")
    shutil.rmtree(project / "sess-1")
    model_usage = {"claude-opus-5-5": {"inputTokens": 1000, "costUSD": 0.004}}
    script(stubs, stream(modelUsage=model_usage))
    out = tmp_path / "out"
    result = run(checkout, stubs, "without", out)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "reconciled yes" in (out / "usage.txt").read_text()
    assert "part main phase - claude-opus-5-5 cost 0.0040000" in (out / "usage.txt").read_text()
