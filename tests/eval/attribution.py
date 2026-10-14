"""SC-003 from a `with` arm's outputs: who wrote the code, and how the phases went.

Usage:  attribution.py <out-dir>
Reads   <out-dir>/status, stream.jsonl, commits.txt and repo/ (the run's
        scratch repository, for the feature's tasks.md).
Prints  one line per clause, `ok` or `FAIL` with what failed, then the main
        session's Bash commands for a reviewer to confirm none writes code.
Exit:   0 every clause holds; 1 one does not; 2 an input cannot be read or
        status is not `ok`.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "NotebookEdit": "notebook_path"}
# The report line, whatever markup the model wraps it in: emphasis and code
# marks are stripped first, then list, quote and heading marks and a closing stop.
REPORT_LINE = re.compile(r"^[\s>#-]*Carried out in this session:\s*(.*?)[\s.]*$", re.MULTILINE)


def heading(line: str) -> str:
    """A phase heading's text, with the heading and emphasis marks around it dropped."""
    return line.strip().lstrip("#*").rstrip("*").strip()


class Unreadable(Exception):
    pass


@dataclass
class Commit:
    subject: str
    files: list[str]


def read_inputs(out: Path) -> tuple[list[dict[str, Any]], list[Commit], str, list[str]]:
    try:
        status = (out / "status").read_text().strip()
        if status != "ok":
            raise Unreadable(f"status is {status!r}, not 'ok'")
        events = [json.loads(line) for line in (out / "stream.jsonl").read_text().splitlines()]
        commits = parse_commits((out / "commits.txt").read_text())
        repo = out / "repo"
        feature = json.loads((repo / ".specify/feature.json").read_text())["feature_directory"]
        tasks = f"{feature}/tasks.md"
        headings = [
            line.strip()
            for line in (repo / tasks).read_text().splitlines()
            if line.startswith("## Phase")
        ]
    except (OSError, ValueError, KeyError) as error:
        raise Unreadable(str(error)) from error
    return events, commits, tasks, headings


def parse_commits(text: str) -> list[Commit]:
    """`git log --format='commit %H%n%s' --name-only`: a header, a subject, the files."""
    commits: list[Commit] = []
    for block in re.split(r"^commit \S+\n", text, flags=re.MULTILINE)[1:]:
        subject, _, files = block.partition("\n")
        commits.append(Commit(subject, [f for f in files.splitlines() if f.strip()]))
    return commits


def main_session_calls(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The main session's tool_use blocks, in order (subagents' have a parent)."""
    calls = []
    for event in events:
        if event.get("type") == "assistant" and event.get("parent_tool_use_id") is None:
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    calls.append(block)
    return calls


def check(
    events: list[dict[str, Any]], commits: list[Commit], tasks: str, headings: list[str]
) -> list[tuple[str, str | None]]:
    """Each clause with None when it holds, else what failed."""
    calls = main_session_calls(events)
    result = next((e for e in events if e.get("type") == "result"), {})
    clauses: list[tuple[str, str | None]] = []

    writes = [
        str(call["input"].get(WRITE_TOOLS[call["name"]], ""))
        for call in calls
        if call["name"] in WRITE_TOOLS
    ]
    outside = [path for path in writes if path != tasks and not path.endswith("/" + tasks)]
    clauses.append(("main session writes only tasks.md", ", ".join(outside) or None))

    sonnet = any("sonnet" in model for model in result.get("modelUsage", {}))
    clauses.append(("modelUsage has a Sonnet entry", None if sonnet else "none"))

    workers = [c for c in calls if c["name"] == "Agent" and c["input"].get("model") == "sonnet"]
    background = [w["id"] for w in workers if w["input"].get("run_in_background") is not False]
    clauses.append(("every worker call in the foreground", ", ".join(background) or None))

    firsts = {
        heading(next(iter(str(w["input"].get("prompt", "")).strip().splitlines()), ""))
        for w in workers
    }
    unopened = [h for h in headings if heading(h) not in firsts]
    clauses.append(("each phase opens a worker's brief", "; ".join(unopened) or None))

    clauses.append(("no worker starts while another is open", overlap(events, workers)))

    code = [c for c in commits if any(f != tasks for f in c.files)]
    unprefixed = [c.subject for c in code if not c.subject.startswith("fixture:")]
    clauses.append(("a commit changes code", None if code else "every commit is tasks.md only"))
    clauses.append(("code commits start with fixture:", "; ".join(unprefixed) or None))

    report = REPORT_LINE.findall(re.sub(r"[*`_]", "", str(result.get("result", ""))))
    said = report[-1] if report else None
    clauses.append(
        (
            "report says Carried out in this session: none",
            None if said == "none" else f"says {said!r}" if report else "line missing",
        )
    )

    denials = result.get("permission_denials") or []
    clauses.append(("no permission denials", f"{len(denials)}" if denials else None))
    return clauses


def overlap(events: list[dict[str, Any]], workers: list[dict[str, Any]]) -> str | None:
    ids = {w["id"] for w in workers}
    open_: set[str] = set()
    for event in events:
        if event.get("parent_tool_use_id") is not None:
            continue
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use" and block.get("id") in ids:
                if open_:
                    return f"{block['id']} started while {', '.join(sorted(open_))} open"
                open_.add(block["id"])
            elif block.get("type") == "tool_result":
                open_.discard(block.get("tool_use_id"))
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        events, commits, tasks, headings = read_inputs(Path(sys.argv[1]))
    except Unreadable as error:
        print(f"attribution.py: {error}", file=sys.stderr)
        return 2
    failed = False
    for clause, failure in check(events, commits, tasks, headings):
        print(f"ok   {clause}" if failure is None else f"FAIL {clause}: {failure}")
        failed = failed or failure is not None
    print("\nmain session's Bash commands:")
    for call in main_session_calls(events):
        if call["name"] == "Bash":
            print(f"  {call['input'].get('command', '')}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
