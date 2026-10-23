"""A deterministic stand-in for the observation rules (specs/004, US2): the git commands the
fragment's Observation bullets name are run, placeholders substituted, in a scratch repository, and
must tell a worker's commits from earlier ones, an empty range from a non-empty one, and a tracked
file from an untracked one.

Usage:  tests/observe_standin.py <fragment.md>
Exit:   0 every command behaves as its bullet says; 1 one does not, or a command is not in the
        fragment; 2 unreadable input

What it proves: the commands exist in the fragment and discriminate as the rules need. What it
does not: that a model runs them (only an eval can show that, README Eval 004).
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}
COMMANDS = {
    "count": r"git rev-list --count .*",
    "log": r"git log --format='%h %s' .*",
    "ancestor": r"git merge-base --is-ancestor .*",
    "tracked": r"git ls-files .*",
    "run": r"git rev-list (?!--count).*",
}


def git(repo: Path, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, shell=True, cwd=repo, env=ENV, capture_output=True, text=True, check=False
    )


def found(text: str) -> dict[str, str]:
    """Each command as the fragment spells it, from the backtick spans of its text."""
    spans = re.findall(r"`([^`]+)`", " ".join(text.split()))
    return {
        name: next((s for s in spans if re.fullmatch(pattern, s)), "")
        for name, pattern in COMMANDS.items()
    }


def check(text: str) -> list[str]:
    commands = found(text)
    problems = [
        f"the fragment does not spell the {n} command" for n, c in commands.items() if not c
    ]
    if problems:
        return problems
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        for step in ("git init -q", "git commit -q --allow-empty -m earlier"):
            git(repo, step)
        earlier = git(repo, "git rev-parse HEAD").stdout.strip()
        (repo / "tracked.txt").write_text("x\n")
        git(repo, "git add tracked.txt && git commit -q -m recorded")
        recorded = git(repo, "git rev-parse HEAD").stdout.strip()
        (repo / "untracked.txt").write_text("y\n")
        for n in (1, 2):
            git(repo, f"git commit -q --allow-empty -m worker-{n}")
        worker = git(repo, "git rev-parse HEAD").stdout.strip()

        def run(name: str, **fill: str) -> subprocess.CompletedProcess[str]:
            command = commands[name].replace("<first recorded HEAD>", fill.get("first", recorded))
            for key, value in {
                "<recorded HEAD>": recorded,
                "<commit>": fill.get("commit", ""),
                "<file>": fill.get("file", ""),
            }.items():
                command = command.replace(key, value)
            return git(repo, command)

        if run("count").stdout.strip() != "2":
            problems.append("the count command does not report the two commits after the record")
        if len(run("log").stdout.strip().splitlines()) != 2:
            problems.append("the log command does not list the two commits after the record")
        if run("ancestor", commit=earlier).returncode != 0:
            problems.append("the ancestor command fails for a commit before the record")
        if run("ancestor", commit=worker).returncode == 0:
            problems.append("the ancestor command succeeds for a commit after the record")
        if run("tracked", file="tracked.txt").returncode != 0:
            problems.append("the tracked-file command fails for a tracked file")
        if run("tracked", file="untracked.txt").returncode == 0:
            problems.append("the tracked-file command succeeds for an untracked file")
        # From the first recorded HEAD (the run's start), the commits of the whole run.
        if len(run("run", first=earlier).stdout.split()) != 3:
            problems.append("the run-range command does not list the run's three commits")
    return problems


def main(argv: list[str]) -> int:
    try:
        text = Path(argv[0]).read_text(encoding="utf-8")
    except (OSError, IndexError) as error:
        print(f"observe_standin.py: {error}", file=sys.stderr)
        return 2
    problems = check(text)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        print("ok: the five observation commands discriminate as the rules need")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
