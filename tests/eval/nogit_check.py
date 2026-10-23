"""E3's pass conditions (specs/004-fragment-form-and-observation): a run in a project that is not
a git repository, read from one run's committed files.

Usage:  nogit_check.py <out-dir>
Reads   <out-dir>/status, versions.txt (`commit`, `fixture`, `no_git`), stream.jsonl,
        heldout.txt, report.txt, repo/<feature>/tasks.md and the fixture's heldout/N as
        committed at the run's commit (tests/eval/fixtures/<fixture>/).
Prints  one line per check, `ok <check>` or `FAIL <check>: <what>`:
          no worker started: no main-session Agent call is briefed with a phase heading
            (the fragment sends a run without git to Fallback; core carries on in the session);
          report says why: the completion report names the missing git repository;
          report carries the Carried out line: `Carried out in this session:` with task ids;
          every task marked, in the run's final tasks.md;
          no question asked;
          held-out N of N.
Exit:   0 every check holds; 1 one does not; 2 unreadable input, or a run that did not count
        (status other than `ok`, or a run with its .git, `no_git` not `yes`).
"""

import json
import re
import sys
from pathlib import Path

import usage
from attribution import heading
from resume_check import FIXTURES, Refused, phases

WHY = re.compile(
    r"not a git repositor|no git repositor|no `?\.git|without (?:a )?`?\.?git|git (?:is )?(?:not|un)",
    re.IGNORECASE,
)


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
        if versions.get("no_git") != "yes":
            raise Refused("the run kept its .git (no_git is not 'yes')")
        commit, fixture = versions["commit"], versions["fixture"]
        feature = json.loads((out / "repo/.specify/feature.json").read_text())["feature_directory"]
        final = (out / "repo" / feature / "tasks.md").read_text()
        n = int(usage.fixture_file(fixtures, commit, f"{fixture}/heldout/N").strip())
        events = [
            json.loads(e) for e in (out / "stream.jsonl").read_text().splitlines() if e.strip()
        ]
        passed = re.match(r"passed (\d+)/", (out / "heldout.txt").read_text())
        report = (out / "report.txt").read_text()
    except (OSError, ValueError, KeyError) as error:
        raise Refused(str(error)) from error
    if not passed:
        raise Refused("heldout.txt has no `passed x/y` line")

    titles = {heading(title) for title, _, _ in phases(final)}
    blocks = [
        block
        for event in events
        if event.get("type") == "assistant" and event.get("parent_tool_use_id") is None
        for block in event.get("message", {}).get("content", [])
        if block.get("type") == "tool_use"
    ]
    briefs = [
        heading(str(b.get("input", {}).get("prompt", "")).split("\n", 1)[0])
        for b in blocks
        if b.get("name") == "Agent"
    ]
    started = [b for b in briefs if b in titles]
    lines = [
        "ok no worker started: core's run"
        if not started
        else f"FAIL no worker started: {started[0]!r} in a project with no git"
    ]
    plain = " ".join(report.replace("*", "").replace("`", "").split())
    lines.append(
        "ok report says why: no git repository"
        if WHY.search(plain)
        else "FAIL report says why: no mention of a missing git repository"
    )
    carried = re.search(r"Carried out in this session:(.*)", report.replace("`", ""))
    lines.append(
        "ok report carries the Carried out line"
        if carried and re.search(r"T\d+", carried.group(1))
        else "FAIL report carries the Carried out line: no `Carried out in this session:` with ids"
    )
    unmarked = sorted(set(re.findall(r"^- \[ \] (T\d+)", final, re.MULTILINE)))
    lines.append(
        "ok every task marked" if not unmarked else f"FAIL every task marked: {', '.join(unmarked)}"
    )
    asked = any(b.get("name") == "AskUserQuestion" for b in blocks)
    lines.append("ok no question asked" if not asked else "FAIL no question asked: AskUserQuestion")
    score = int(passed.group(1))
    lines.append(
        f"ok held-out N of N ({n})" if score == n else f"FAIL held-out N of N: {score}/{n}"
    )
    return lines


def main(argv: list[str], fixtures: Path = FIXTURES) -> int:
    try:
        lines = check(Path(argv[0]), fixtures)
    except Refused as error:
        print(f"nogit_check.py: refused: {error}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0 if all(line.startswith("ok ") for line in lines) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
