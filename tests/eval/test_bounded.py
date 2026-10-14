"""bounded.py: a command under a deadline, its whole process group killed past it."""

import os
import subprocess
import sys
import time
from pathlib import Path

BOUNDED = Path(__file__).with_name("bounded.py")


def bounded(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BOUNDED), *argv],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_a_command_that_ends_in_time_returns_its_status() -> None:
    assert bounded("10", "sh", "-c", "exit 3").returncode == 3


def test_past_the_deadline_the_whole_group_dies_and_the_exit_is_124(tmp_path: Path) -> None:
    # The grandchild ignores SIGTERM (an ignored signal survives exec), so only
    # the SIGKILL after the grace period ends it: the group, not just the child.
    pidfile = tmp_path / "pid"
    started = time.monotonic()
    result = bounded("1", "sh", "-c", f'trap "" TERM; sleep 60 & echo $! > {pidfile}; wait')
    assert result.returncode == 124
    assert time.monotonic() - started < 20
    pid = int(pidfile.read_text())
    for _ in range(40):
        if not alive(pid):
            break
        time.sleep(0.05)
    assert not alive(pid)


def test_a_missing_command_exits_127() -> None:
    assert bounded("10", "no-such-command-for-bounded").returncode == 127
