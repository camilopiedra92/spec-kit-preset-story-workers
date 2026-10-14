"""oracle.sh: a fixture's held-out tests against its reference implementation.

Each test builds a throwaway checkout with a one-function fixture, so what
oracle.sh copies and counts is under the test's control. The fixture runs with
the interpreter running these tests (a stub `uv` that execs `python -m`), not a
synced virtualenv: what is under test is the script, not uv.
"""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
BASH = shutil.which("bash") or "/bin/bash"

UV = f"""#!/bin/sh
[ "$1" = run ] && shift
[ "$1" = --locked ] && shift
exec {sys.executable} -m "$@"
"""

HELDOUT = """import importlib


def test_one() -> None:
    assert importlib.import_module("greet").greet() == "hi"


def test_two() -> None:
    assert importlib.import_module("greet").greet().upper() == "HI"
"""


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = tmp_path / "checkout"
    eval_dir = root / "tests/eval"
    eval_dir.mkdir(parents=True)
    shutil.copy2(HERE / "oracle.sh", eval_dir / "oracle.sh")
    fixture = eval_dir / "fixtures/greet"
    (fixture / "project/src").mkdir(parents=True)
    (fixture / "project/pyproject.toml").write_text(
        '[project]\nname = "greet"\nversion = "0"\n\n'
        '[tool.pytest.ini_options]\npythonpath = ["src"]\n'
    )
    (fixture / "heldout").mkdir()
    (fixture / "heldout/test_greet.py").write_text(HELDOUT)
    (fixture / "heldout/N").write_text("2\n")
    (fixture / "reference/src").mkdir(parents=True)
    (fixture / "reference/src/greet.py").write_text('def greet() -> str:\n    return "hi"\n')
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "checkout"], check=True)
    return root


@pytest.fixture
def stubs(tmp_path: Path) -> Path:
    bin_ = tmp_path / "stubs"
    bin_.mkdir()
    uv = bin_ / "uv"
    uv.write_text(UV)
    uv.chmod(uv.stat().st_mode | stat.S_IXUSR)
    return bin_


def oracle(
    checkout: Path, stubs: Path, *args: str, fixture: str = "greet"
) -> subprocess.CompletedProcess[str]:
    env = {"HOME": os.environ["HOME"], "PATH": f"{stubs}:{os.environ['PATH']}"}
    return subprocess.run(
        [BASH, str(checkout / "tests/eval/oracle.sh"), *args, fixture],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


def commit(checkout: Path) -> None:
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(checkout)]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "change"], check=True)


def test_a_correct_reference_passes_with_the_recorded_count(checkout: Path, stubs: Path) -> None:
    result = oracle(checkout, stubs)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed 2/2 (N 2)" in result.stdout


def test_a_wrong_reference_fails(checkout: Path, stubs: Path) -> None:
    ref = checkout / "tests/eval/fixtures/greet/reference/src/greet.py"
    ref.write_text('def greet() -> str:\n    return "ho"\n')
    commit(checkout)
    result = oracle(checkout, stubs)
    assert result.returncode == 1
    assert "passed 0/2" in result.stdout


def test_a_count_that_differs_from_n_fails(checkout: Path, stubs: Path) -> None:
    (checkout / "tests/eval/fixtures/greet/heldout/N").write_text("3\n")
    commit(checkout)
    result = oracle(checkout, stubs)
    assert result.returncode == 1
    assert "N 3" in result.stdout


def test_write_n_records_the_collected_count(checkout: Path, stubs: Path) -> None:
    n = checkout / "tests/eval/fixtures/greet/heldout/N"
    n.unlink()
    commit(checkout)
    result = oracle(checkout, stubs, "--write-n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert n.read_text() == "2\n"


def test_missing_n_without_write_n_is_refused(checkout: Path, stubs: Path) -> None:
    (checkout / "tests/eval/fixtures/greet/heldout/N").unlink()
    commit(checkout)
    assert oracle(checkout, stubs).returncode == 2


@pytest.mark.parametrize("fixture", ["nowhere", "../greet", ""])
def test_an_unknown_fixture_is_refused(checkout: Path, stubs: Path, fixture: str) -> None:
    result = oracle(checkout, stubs, fixture=fixture)
    assert result.returncode == 2
    assert "fixture" in result.stderr


def test_uncommitted_changes_stay_out_of_the_copy(checkout: Path, stubs: Path) -> None:
    # The committed fixture is what an arm gets; an edit in progress is not.
    stray = checkout / "tests/eval/fixtures/greet/reference/src/greet.py"
    stray.write_text('def greet() -> str:\n    return "ho"\n')
    result = oracle(checkout, stubs)
    assert result.returncode == 0, result.stdout + result.stderr


def test_write_n_does_not_record_a_count_from_a_failing_run(checkout: Path, stubs: Path) -> None:
    n = checkout / "tests/eval/fixtures/greet/heldout/N"
    n.unlink()
    ref = checkout / "tests/eval/fixtures/greet/reference/src/greet.py"
    ref.write_text('def greet() -> str:\n    return "ho"\n')
    commit(checkout)
    assert oracle(checkout, stubs, "--write-n").returncode == 1
    assert not n.exists()
