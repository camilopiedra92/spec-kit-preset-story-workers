"""Runs a command under a deadline and kills its whole process group past it.

macOS ships no `timeout`, and killing only the child leaves its children
running: a headless `claude` starts tools that outlive it.

Usage:  bounded.py <seconds> <command> [args...]
Exit:   the command's status (128 + n when signal n ended it); 124 past the
        deadline; 127 when the command cannot be started.
"""

import os
import signal
import subprocess
import sys

GRACE_SECONDS = 5.0


def run(deadline: float, argv: list[str]) -> int:
    try:
        # Its own session, so its process group is the command and every
        # descendant that has not left it.
        child = subprocess.Popen(argv, start_new_session=True)
    except (FileNotFoundError, PermissionError):
        print(f"bounded.py: cannot run {argv[0]}", file=sys.stderr)
        return 127
    try:
        status = child.wait(timeout=deadline)
    except subprocess.TimeoutExpired:
        kill_group(child)
        return 124
    return 128 - status if status < 0 else status


def kill_group(child: "subprocess.Popen[bytes]") -> None:
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass
    # The child may have exited on SIGTERM while a descendant ignored it; the
    # group outlives its leader, so it is killed whether or not the child is.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait()


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    return run(float(sys.argv[1]), sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
