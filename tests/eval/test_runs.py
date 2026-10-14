"""runs.sh: one confirmed step of the eval, against stub run.sh, compare.py and claude.

Each test copies runs.sh into a throwaway tests/eval beside stubs of run.sh
(its exit codes scripted per call in run.plan, its calls logged in run.calls)
and compare.py (its --gate exit in gate.exit), with a stub `claude` on PATH
that prints the version in claude.version.
"""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).parent
BASH = shutil.which("bash") or "/bin/bash"

RUN = r"""#!/usr/bin/env bash
# Stub run.sh: the next exit code from run.plan (default 0); writes what the
# real one would leave for that code.
here=$(cd "$(dirname "$0")" && pwd)
echo "$*" >> "$here/run.calls"
out=${!#}
code=$(head -n 1 "$here/run.plan" 2> /dev/null)
code=${code:-0}
[ -s "$here/run.plan" ] && sed -i.bak 1d "$here/run.plan"
# A try that reached the agent leaves a stream: it spent usage.
case $code in
  0) mkdir -p "$out"; echo ok > "$out/status"; : > "$out/stream.jsonl" ;;
  1) mkdir -p "$out"; echo "not counted: exit 1" > "$out/status"; : > "$out/stream.jsonl" ;;
  2) echo "run.sh: refused before anything" >&2 ;;
  3) mkdir -p "$out"; echo "refused: versions differ from the baseline: claude" > "$out/status"
     exit 2 ;;
esac
exit "$code"
"""

COMPARE = r"""import sys
from pathlib import Path

here = Path(__file__).parent
(here / "gate.calls").write_text(" ".join(sys.argv[1:]))
gate = here / "gate.exit"
code = int(gate.read_text()) if gate.exists() else 0
if code == 2:
    print("compare.py: refused: without-2: status is 'x'", file=sys.stderr)
sys.exit(code)
"""

CLAUDE = r"""#!/bin/sh
[ "$1" = --version ] && { echo "$(cat "$(dirname "$0")/claude.version") (Claude Code)"; exit 0; }
exit 9
"""


def executable(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def ev(tmp_path: Path) -> Path:
    eval_dir = tmp_path / "tests/eval"
    eval_dir.mkdir(parents=True)
    shutil.copy2(HERE / "runs.sh", eval_dir / "runs.sh")
    executable(eval_dir / "run.sh", RUN)
    (eval_dir / "compare.py").write_text(COMPARE)
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    executable(bin_ / "claude", CLAUDE)
    (bin_ / "claude.version").write_text("2.1.299\n")
    return eval_dir


@pytest.fixture
def attempt(tmp_path: Path) -> Path:
    a = tmp_path / "attempt-1"
    a.mkdir()
    (a / "probes.txt").write_text(
        "claude 2.1.299 (Claude Code)\nok   R1 1: x\nok   R1 3: y\nprobes: 2 ok, 0 FAIL\n"
    )
    return a


def runs(ev: Path, attempt: Path, *arms: str) -> subprocess.CompletedProcess[str]:
    bin_ = ev.parent.parent / "bin"
    env = {"HOME": str(ev.parent.parent), "PATH": f"{bin_}:{os.environ['PATH']}"}
    return subprocess.run(
        [BASH, str(ev / "runs.sh"), str(attempt), "checkout", *arms],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


def calls(ev: Path) -> list[str]:
    path = ev / "run.calls"
    return path.read_text().splitlines() if path.exists() else []


def plan(ev: Path, *codes: int) -> None:
    (ev / "run.plan").write_text("".join(f"{c}\n" for c in codes))


def test_three_counted_runs_per_arm_alternating(ev: Path, attempt: Path) -> None:
    result = runs(ev, attempt, "with", "fallback")
    assert result.returncode == 0, result.stdout + result.stderr
    order = [c.split()[-1].rsplit("/", 1)[-1] for c in calls(ev)]
    assert order == [
        "with-1-1", "fallback-1-1", "with-2-1", "fallback-2-1", "with-3-1", "fallback-3-1",
    ]  # fmt: skip
    for name in ("with-1", "with-2", "with-3", "fallback-1", "fallback-2", "fallback-3"):
        link = attempt / name
        assert link.is_symlink() and not os.readlink(link).startswith("/"), name
        assert (link / "status").read_text() == "ok\n"


def test_a_run_gets_at_most_three_tries(ev: Path, attempt: Path) -> None:
    plan(ev, 1, 1, 1)
    result = runs(ev, attempt, "without")
    assert result.returncode == 1
    assert len(calls(ev)) == 3
    assert not (attempt / "without-1").exists()


def test_a_rerun_that_counts_is_linked(ev: Path, attempt: Path) -> None:
    plan(ev, 1, 0)
    assert runs(ev, attempt, "without").returncode == 0
    assert os.readlink(attempt / "without-1") == "without-1-2"


def test_the_baseline_is_passed_once_without_1_exists(ev: Path, attempt: Path) -> None:
    assert runs(ev, attempt, "without").returncode == 0
    first, *rest = calls(ev)
    assert "--baseline" not in first
    baseline = f"--baseline {attempt}/without-1 "
    assert rest and all(c.startswith(baseline) for c in rest), rest


@pytest.mark.parametrize(
    ("breaking", "reason"),
    [
        ("missing", "probes.txt"),
        ("failed", "probe"),
        ("version", "version"),
        ("truncated", "probe"),
    ],
)
def test_the_probes_must_hold_before_every_try(
    ev: Path, attempt: Path, breaking: str, reason: str
) -> None:
    probes = attempt / "probes.txt"
    if breaking == "missing":
        probes.unlink()
    elif breaking == "failed":
        probes.write_text(
            "claude 2.1.299 (Claude Code)\nok   R1 1: x\nFAIL R1 5: x\nprobes: 1 ok, 1 FAIL\n"
        )
    elif breaking == "truncated":
        probes.write_text("claude 2.1.299 (Claude Code)\nok   R1 1: x\n")
    else:
        (ev.parent.parent / "bin/claude.version").write_text("2.1.300\n")
    result = runs(ev, attempt, "without")
    assert result.returncode == 2
    assert calls(ev) == []
    status = (attempt / "without-1-1/status").read_text()
    assert status.startswith("refused") and reason in status, status


def test_a_version_change_mid_set_stops_before_the_next_try(ev: Path, attempt: Path) -> None:
    plan(ev, 0, 0)
    version = ev.parent.parent / "bin/claude.version"
    # The stub run.sh cannot change the version, so the test changes it between
    # two invocations: the first set's three runs, then a second arm.
    assert runs(ev, attempt, "without").returncode == 0
    version.write_text("2.1.300\n")
    (ev / "gate.exit").write_text("0\n")
    result = runs(ev, attempt, "with")
    assert result.returncode == 2
    assert (attempt / "with-1-1/status").read_text().startswith("refused")


def test_with_and_fallback_need_an_open_gate(ev: Path, attempt: Path) -> None:
    assert runs(ev, attempt, "without").returncode == 0
    (ev / "gate.exit").write_text("1\n")
    before = len(calls(ev))
    result = runs(ev, attempt, "with", "fallback")
    assert result.returncode == 2
    assert len(calls(ev)) == before
    assert "gate" in (attempt / "with-1-1/status").read_text()
    gate_args = (ev / "gate.calls").read_text().split()
    assert gate_args[0] == "--gate" and len(gate_args) == 4


def test_without_does_not_consult_the_gate(ev: Path, attempt: Path) -> None:
    (ev / "gate.exit").write_text("1\n")
    assert runs(ev, attempt, "without").returncode == 0
    assert not (ev / "gate.calls").exists()


def test_run_sh_refusing_before_its_out_dir_leaves_a_status(ev: Path, attempt: Path) -> None:
    plan(ev, 2)
    result = runs(ev, attempt, "without")
    assert result.returncode == 2
    assert len(calls(ev)) == 1
    status = (attempt / "without-1-1/status").read_text()
    assert status.startswith("refused") and "refused before anything" in status


def test_run_sh_refusing_with_its_own_status_keeps_it(ev: Path, attempt: Path) -> None:
    plan(ev, 0, 3)
    assert runs(ev, attempt, "without").returncode == 2
    assert len(calls(ev)) == 2
    assert "versions differ" in (attempt / "without-2-1/status").read_text()


def test_a_refusal_that_spent_nothing_does_not_end_the_attempt(ev: Path, attempt: Path) -> None:
    probes = attempt / "probes.txt"
    text = probes.read_text()
    probes.unlink()
    assert runs(ev, attempt, "without").returncode == 2
    assert (attempt / "without-1-1/status").read_text().startswith("refused")
    probes.write_text(text)
    result = runs(ev, attempt, "without")
    assert result.returncode == 0, result.stdout + result.stderr
    # The refused try spent nothing: run 1 still has its three tries.
    assert os.readlink(attempt / "without-1") == "without-1-2"


def test_the_rerun_bound_holds_across_invocations(ev: Path, attempt: Path) -> None:
    plan(ev, 0, 1, 1, 1)
    assert runs(ev, attempt, "without").returncode == 1
    before = len(calls(ev))
    assert runs(ev, attempt, "without").returncode == 1
    assert len(calls(ev)) == before  # run 2 spent its three tries; run 1 stays linked


def test_a_counted_run_is_not_run_again(ev: Path, attempt: Path) -> None:
    plan(ev, 0, 2)
    assert runs(ev, attempt, "without").returncode == 2  # run 2 refused before its dir
    assert runs(ev, attempt, "without").returncode == 0
    names = [c.split()[-1].rsplit("/", 1)[-1] for c in calls(ev)]
    assert names == ["without-1-1", "without-2-1", "without-2-2", "without-3-1"]


def test_without_with_another_arm_is_refused(ev: Path, attempt: Path) -> None:
    result = runs(ev, attempt, "without", "with")
    assert result.returncode == 2
    assert calls(ev) == []


def test_a_refused_gate_keeps_its_reason(ev: Path, attempt: Path) -> None:
    assert runs(ev, attempt, "without").returncode == 0
    (ev / "gate.exit").write_text("2\n")
    assert runs(ev, attempt, "with").returncode == 2
    assert "gate" in (attempt / "with-1-1/status").read_text()
    assert "compare.py" in (attempt / "with-1-1/status").read_text()


@pytest.mark.parametrize("args", [[], ["sideways"], ["with", "with"]])
def test_bad_arguments_are_refused(ev: Path, attempt: Path, args: list[str]) -> None:
    result = runs(ev, attempt, *args)
    assert result.returncode == 2
    assert calls(ev) == []


REAL_GATE_RUN = r"""#!/usr/bin/env bash
# Stub run.sh writing a counted `without` run in the files compare.py reads; the
# held-out score comes from heldout.plan, one line per call.
here=$(cd "$(dirname "$0")" && pwd)
echo "$*" >> "$here/run.calls"
out=${!#}
passed=$(head -n 1 "$here/heldout.plan"); sed -i.bak 1d "$here/heldout.plan"
mkdir -p "$out"
echo ok > "$out/status"
: > "$out/stream.jsonl"
printf 'commit: %s\nfixture: fx\narm: %s\ndate: d\n' "$(cat "$here/commit.sha")" \
  "$(echo "$*" | awk '{print $(NF-1)}')" > "$out/versions.txt"
echo "passed $passed/2" > "$out/heldout.txt"
echo "exit: 0" > "$out/suite.txt"
echo '{"models": {}, "parts": []}' > "$out/usage.json"
: > "$out/models.txt"; : > "$out/report.txt"
"""


def test_the_gate_is_the_real_compare_py(ev: Path, attempt: Path) -> None:
    for name in ("compare.py", "attribution.py", "usage.py"):
        shutil.copy2(HERE / name, ev / name)
    executable(ev / "run.sh", REAL_GATE_RUN)
    project = ev / "fixtures/fx/project"
    (project / "specs/001-fx").mkdir(parents=True)
    (project / ".specify").mkdir()
    (project / ".specify/feature.json").write_text('{"feature_directory": "specs/001-fx"}\n')
    (project / "specs/001-fx/spec.md").write_text("### User Story 1 - A (Priority: P1)\n")
    (project / "specs/001-fx/tasks.md").write_text("- [ ] T001 a\n")
    (ev / "fixtures/fx/heldout").mkdir()
    (ev / "fixtures/fx/heldout/N").write_text("2\n")
    (ev / "heldout.plan").write_text("2\n2\n2\n2\n")
    # compare.py reads the fixture as committed at the runs' commit.
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(ev)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "fixtures"], check=True)
    subprocess.run([*git, "commit", "-qm", "fixture"], check=True)
    sha = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    (ev / "commit.sha").write_text(sha.stdout)
    assert runs(ev, attempt, "without").returncode == 0
    # Every without run perfect: the real gate is closed, so `with` is refused.
    result = runs(ev, attempt, "with")
    assert result.returncode == 2
    assert "gate closed" in (attempt / "with-1-1/status").read_text()
