"""E2's checks (specs/004-fragment-form-and-observation): did the main session observe each
worker with git, read from one run's committed files.

Usage:  observe_check.py <out-dir>
Reads   <out-dir>/status, stream.jsonl, report.txt, repo/<feature>/tasks.md (for the phase
        headings that tell a worker's brief from a review's prompt).
Prints  `ok <check>` or `FAIL <check>: <what>` per check, then `info` lines, which describe
        and decide nothing:
          range read after every worker: after each worker's Agent call and before the next
            worker's, the main session ran `git log` or `git rev-list` over a range (`A..B`);
          Carried out line present: the report carries `Carried out in this session:`;
          info: how many `git merge-base --is-ancestor` and `git ls-files --error-unmatch`
            commands ran, and the Carried out line.
What it cannot show: that an observation caught a wrong report. The eval's workers are not told
to misreport, so it shows that the observation was made, not that it found anything.
Exit:   0 every check holds; 1 one does not; 2 unreadable input or an uncounted run.
"""

import json
import re
import sys
from pathlib import Path

from attribution import heading
from resume_check import Refused, phases

RANGE = re.compile(r"git\s+(?:log|rev-list)\b[^\n;&|]*\.\.")
CITED = re.compile(r"git\s+(?:merge-base\s+--is-ancestor|ls-files\s+--error-unmatch)\b")


def check(out: Path) -> list[str]:
    try:
        status = (out / "status").read_text().strip()
        if status != "ok":
            raise Refused(f"status is {status!r}, not 'ok'")
        feature = json.loads((out / "repo/.specify/feature.json").read_text())["feature_directory"]
        final = (out / "repo" / feature / "tasks.md").read_text()
        events = [
            json.loads(e) for e in (out / "stream.jsonl").read_text().splitlines() if e.strip()
        ]
        report = (out / "report.txt").read_text()
    except (OSError, ValueError, KeyError) as error:
        raise Refused(str(error)) from error

    titles = {heading(title) for title, _, _ in phases(final)}
    # In order: each worker (an Agent call briefed with a phase heading) opens a segment of
    # the main session's later Bash commands, up to the next worker.
    segments: list[list[str]] = []
    commands: list[str] = []
    for event in events:
        if event.get("type") != "assistant" or event.get("parent_tool_use_id") is not None:
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            args = block.get("input", {})
            if block.get("name") == "Agent":
                if heading(str(args.get("prompt", "")).split("\n", 1)[0]) in titles:
                    segments.append([])
            elif block.get("name") == "Bash":
                command = str(args.get("command", ""))
                commands.append(command)
                if segments:
                    segments[-1].append(command)
    if not segments:
        raise Refused("no worker started: nothing to observe")
    unread = [i + 1 for i, seg in enumerate(segments) if not any(RANGE.search(c) for c in seg)]
    lines = [
        f"ok range read after every worker ({len(segments)})"
        if not unread
        else f"FAIL range read after every worker: none after worker(s) {unread}"
    ]
    carried = re.search(r"Carried out in this session:(.*)", report.replace("`", ""))
    lines.append(
        "ok Carried out line present"
        if carried
        else "FAIL Carried out line present: no `Carried out in this session:`"
    )
    cited = sum(1 for c in commands if CITED.search(c))
    lines.append(f"info cited-evidence commands (merge-base --is-ancestor, ls-files): {cited}")
    lines.append(f"info Carried out line:{carried.group(1) if carried else ' (none)'}")
    return lines


def main(argv: list[str]) -> int:
    try:
        lines = check(Path(argv[0]))
    except Refused as error:
        print(f"observe_check.py: refused: {error}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0 if not any(line.startswith("FAIL ") for line in lines) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
