"""The resume eval's pass conditions, read from one run's committed files.

Usage:  resume_check.py <out-dir>
Reads   <out-dir>/status, versions.txt (`commit`, `fixture`, `state`), commits.txt,
        stream.jsonl, heldout.txt and report.txt, and the fixture and its state as
        committed at the run's commit (tests/eval/fixtures/<fixture>/).
Prints  one line per check, `ok <check>` or `FAIL <check>: <what>`:
          finished phases untouched: no commit of the run changes a file that only
            the state's finished phases name;
          first brief opens the first unfinished phase;
          held-out N of N;
          report names the resume: a `Resumed at phase <n>` line for that phase.
Exit:   0 every check holds; 1 one does not; 2 unreadable input, or a run that did
        not count (status other than `ok`).

The contract is specs/003-resume-from-head/contracts/harness.md; research R3 there.
"""

import json
import re
import sys
from pathlib import Path

import usage
from attribution import heading, parse_commits

FIXTURES = Path(__file__).parent / "fixtures"
TASK = re.compile(r"^- \[([ xX])\] T\d+")
PATH = re.compile(r"`((?:src|tests)/[^`]+)`")


class Refused(Exception):
    pass


def phases(tasks: str) -> list[tuple[str, bool, set[str]]]:
    """Each phase's heading, whether all its tasks are marked, and the files they name."""
    found: list[tuple[str, bool, set[str]]] = []
    for line in tasks.splitlines():
        if line.startswith("## Phase"):
            found.append((line.strip(), True, set()))
        elif found and (task := TASK.match(line)):
            title, done, files = found[-1]
            found[-1] = (title, done and task.group(1) != " ", files | set(PATH.findall(line)))
    return found


def check(out: Path, fixtures: Path) -> list[str]:
    try:
        status = (out / "status").read_text().strip()
        if status != "ok":
            raise Refused(f"status is {status!r}, not 'ok'")
        versions = {
            k: v
            for k, _, v in (
                line.partition(": ") for line in (out / "versions.txt").read_text().splitlines()
            )
        }
        commit, fixture, state = versions["commit"], versions["fixture"], versions["state"]
        project = f"{fixture}/project"
        feature = json.loads(
            usage.fixture_file(fixtures, commit, f"{project}/.specify/feature.json")
        )["feature_directory"]
        tasks = usage.fixture_file(fixtures, commit, f"{fixture}/states/{state}/{feature}/tasks.md")
        n = int(usage.fixture_file(fixtures, commit, f"{fixture}/heldout/N").strip())
        commits = parse_commits((out / "commits.txt").read_text())
        events = [
            json.loads(e) for e in (out / "stream.jsonl").read_text().splitlines() if e.strip()
        ]
        passed = re.match(r"passed (\d+)/", (out / "heldout.txt").read_text())
        report = (out / "report.txt").read_text()
    except (OSError, ValueError, KeyError) as error:
        raise Refused(str(error)) from error
    if not passed:
        raise Refused("heldout.txt has no `passed x/y` line")

    all_phases = phases(tasks)
    finished = set().union(*(files for _, done, files in all_phases if done))
    open_files = set().union(*(files for _, done, files in all_phases if not done))
    finished_only = finished - open_files
    first_open = next((i for i, (_, done, _) in enumerate(all_phases) if not done), None)
    if first_open is None:
        raise Refused("the state marks every task done: nothing to resume")
    title = all_phases[first_open][0]
    number = re.match(r"## Phase (\d+)", title)

    lines = []
    touched = sorted({f for c in commits for f in c.files if f in finished_only})
    lines.append(
        "ok finished phases untouched"
        if not touched
        else f"FAIL finished phases untouched: {', '.join(touched)}"
    )
    briefs = [
        str(block.get("input", {}).get("prompt", ""))
        for event in events
        if event.get("type") == "assistant" and event.get("parent_tool_use_id") is None
        for block in event.get("message", {}).get("content", [])
        if block.get("type") == "tool_use"
        and block.get("name") == "Agent"
        and block.get("input", {}).get("model") == "sonnet"
    ]
    first = heading(briefs[0].split("\n", 1)[0]) if briefs else "(no worker)"
    lines.append(
        "ok first brief opens the first unfinished phase"
        if first == heading(title)
        else f"FAIL first brief opens the first unfinished phase: {first!r}, not {heading(title)!r}"
    )
    score = int(passed.group(1))
    lines.append(
        f"ok held-out N of N ({n})" if score == n else f"FAIL held-out N of N: {score}/{n}"
    )
    named = re.search(r"Resumed at phase (\d+)", report.replace("*", "").replace("`", ""))
    want = number.group(1) if number else "?"
    lines.append(
        "ok report names the resume"
        if named and named.group(1) == want
        else f"FAIL report names the resume: want phase {want}, "
        f"found {named.group(0) if named else 'none'}"
    )
    return lines


def main(argv: list[str], fixtures: Path = FIXTURES) -> int:
    try:
        lines = check(Path(argv[0]), fixtures)
    except Refused as error:
        print(f"resume_check.py: refused: {error}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0 if all(line.startswith("ok ") for line in lines) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
