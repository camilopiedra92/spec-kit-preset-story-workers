"""The resume eval's pass conditions, read from one run's committed files.

Usage:  resume_check.py <out-dir>
Reads   <out-dir>/status, versions.txt (`commit`, `fixture`, `state`), commits.txt,
        stream.jsonl, heldout.txt, report.txt and repo/<feature>/tasks.md, and the
        fixture and its state as committed at the run's commit
        (tests/eval/fixtures/<fixture>/).
Prints  one line per check, `ok <check>` or `FAIL <check>: <what>`:
          finished phases untouched: no commit of the run changes a file the state
            holds that no unfinished phase's task names;
          first brief opens the first unfinished phase;
          no brief opens a finished phase;
          every task marked, in the run's final tasks.md;
          no question asked: no AskUserQuestion call in the stream;
          held-out N of N;
          report names the start: the fragment's `Started at phase <n>: ...` line, for
            that phase.
Exit:   0 every check holds; 1 one does not; 2 unreadable input, or a run that did
        not count (status other than `ok`).

The contract is specs/003-resume-from-head/contracts/harness.md; research R3 there.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import usage
from attribution import heading, parse_commits

FIXTURES = Path(__file__).parent / "fixtures"
STARTED = (
    "Started at phase {n}: work committed before this run was covered by the whole suite, "
    "not read as a diff, its static-check findings in the baseline."
)
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


def state_files(fixtures: Path, commit: str, state_dir: str) -> set[str]:
    """The files a state holds at `commit`, relative to the project it is laid over."""
    listed = subprocess.run(
        ["git", "-C", str(fixtures), "ls-tree", "-r", "--name-only", commit, "--", f"{state_dir}/"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return {name.removeprefix(f"{state_dir}/") for name in listed}


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
        state_dir = f"{fixture}/states/{state}"
        tasks = usage.fixture_file(fixtures, commit, f"{state_dir}/{feature}/tasks.md")
        held = state_files(fixtures, commit, state_dir) - {f"{feature}/tasks.md"}
        final = (out / "repo" / feature / "tasks.md").read_text()
        n = int(usage.fixture_file(fixtures, commit, f"{fixture}/heldout/N").strip())
        commits = parse_commits((out / "commits.txt").read_text())
        events = [
            json.loads(e) for e in (out / "stream.jsonl").read_text().splitlines() if e.strip()
        ]
        passed = re.match(r"passed (\d+)/", (out / "heldout.txt").read_text())
        report = (out / "report.txt").read_text()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        raise Refused(str(error)) from error
    if not passed:
        raise Refused("heldout.txt has no `passed x/y` line")

    all_phases = phases(tasks)
    # The state holds what the finished phases left, whatever tasks.md calls each file;
    # a file an unfinished phase names (a shared module) is that phase's to change too.
    open_files = set().union(*(files for _, done, files in all_phases if not done))
    finished_only = held - open_files
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
    opened = [heading(b.split("\n", 1)[0]) for b in briefs]
    first = opened[0] if opened else "(no worker)"
    lines.append(
        "ok first brief opens the first unfinished phase"
        if first == heading(title)
        else f"FAIL first brief opens the first unfinished phase: {first!r}, not {heading(title)!r}"
    )
    done_titles = {heading(t) for t, done, _ in all_phases if done}
    redone = sorted({o for o in opened if o in done_titles})
    lines.append(
        "ok no brief opens a finished phase"
        if not redone
        else f"FAIL no brief opens a finished phase: {', '.join(redone)}"
    )
    unmarked = re.findall(r"^- \[ \] (T\d+)", final, re.MULTILINE)
    lines.append(
        "ok every task marked" if not unmarked else f"FAIL every task marked: {', '.join(unmarked)}"
    )
    asked = any(
        block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion"
        for event in events
        if event.get("type") == "assistant"
        for block in event.get("message", {}).get("content", [])
    )
    lines.append("ok no question asked" if not asked else "FAIL no question asked: AskUserQuestion")
    score = int(passed.group(1))
    lines.append(
        f"ok held-out N of N ({n})" if score == n else f"FAIL held-out N of N: {score}/{n}"
    )
    want = STARTED.format(n=number.group(1) if number else "?")
    plain = " ".join(report.replace("*", "").replace("`", "").split())
    lines.append(
        "ok report names the start"
        if want in plain
        else f"FAIL report names the start: no line {want!r}"
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
