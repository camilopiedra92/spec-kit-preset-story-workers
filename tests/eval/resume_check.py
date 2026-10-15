"""The resume eval's pass conditions, read from one run's committed files.

Usage:  resume_check.py <out-dir>
Reads   <out-dir>/status, versions.txt (`commit`, `fixture`, `state`), commits.txt,
        stream.jsonl, heldout.txt, report.txt and repo/<feature>/tasks.md, and the
        fixture and its state as committed at the run's commit
        (tests/eval/fixtures/<fixture>/).
Prints  one line per check, `ok <check>` or `FAIL <check>: <what>`:
          finished phases untouched: a file the state's committed/ holds that no
            unfinished phase's task names is in no commit of the run, and the run's
            tree holds it as the state does;
          uncommitted changes untouched: each file of the state's uncommitted/ is in
            no commit of the run, and the run's tree holds it as the state does;
          first brief opens the first unfinished phase;
          no brief opens a finished phase;
          every task marked, in the run's final tasks.md;
          no question asked: no AskUserQuestion call in the stream;
          held-out N of N;
          report names the start: the fragment's `Started at phase <n>: ...` line, for
            that phase;
          feature-directory tasks carried out in this session: each unmarked task that
            names a file in the feature directory is on the report's `Carried out in
            this session:` line, its files changed in the tree and in no commit.
        When the state leaves work uncommitted outside the feature directory, the run
        is core's: `no worker started` replaces the first-brief check, and `report names
        the paths outside the feature directory` replaces the start line. A state may
        extend another (its `extends` file), laid over it as run.sh lays them.
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


def layers(fixtures: Path, commit: str, fixture: str, state: str) -> list[str]:
    """The state and the states it extends, base first, as run.sh lays them."""
    chain = [state]
    while len(chain) <= 5:
        try:
            base = usage.fixture_file(
                fixtures, commit, f"{fixture}/states/{chain[0]}/extends"
            ).strip()
        except ValueError:
            return chain
        chain.insert(0, base)
    raise Refused(f"state {state!r} extends more than 5 deep")


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
        # No state (`state: -`): a fresh run on the fixture's project as committed.
        names = [] if state == "-" else layers(fixtures, commit, fixture, state)
        dirs = [f"{fixture}/states/{name}" for name in names]
        parts = {
            part: {d: state_files(fixtures, commit, f"{d}/{part}") for d in dirs}
            for part in ("committed", "uncommitted")
        }

        def layered(part: str, name: str) -> str:
            """A state file as the last layer holding it lays it."""
            top = next(d for d in reversed(dirs) if name in parts[part][d])
            return usage.fixture_file(fixtures, commit, f"{top}/{part}/{name}")

        has_tasks = any(f"{feature}/tasks.md" in parts["committed"][d] for d in dirs)
        tasks = (
            layered("committed", f"{feature}/tasks.md")
            if has_tasks
            else usage.fixture_file(fixtures, commit, f"{project}/{feature}/tasks.md")
        )
        held = set().union(*parts["committed"].values()) - {f"{feature}/tasks.md"}
        left = set().union(*parts["uncommitted"].values())
        final = (out / "repo" / feature / "tasks.md").read_text()
        n = int(usage.fixture_file(fixtures, commit, f"{fixture}/heldout/N").strip())
        commits = parse_commits((out / "commits.txt").read_text())
        events = [
            json.loads(e) for e in (out / "stream.jsonl").read_text().splitlines() if e.strip()
        ]
        passed = re.match(r"passed (\d+)/", (out / "heldout.txt").read_text())
        report = (out / "report.txt").read_text()
    except (OSError, ValueError, KeyError, StopIteration, subprocess.CalledProcessError) as error:
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

    def as_state(part: str, name: str) -> bool:
        tree = out / "repo" / name
        return tree.is_file() and tree.read_text() == layered(part, name)

    def before(name: str) -> str | None:
        """A file as the run found it: the state's, else the project's, else none."""
        if name in held:
            return layered("committed", name)
        if name == f"{feature}/tasks.md":
            return tasks
        try:
            return usage.fixture_file(fixtures, commit, f"{project}/{name}")
        except ValueError:
            return None

    # Uncommitted work outside the feature directory sends the whole run to core.
    outside = sorted(f for f in left if not f.startswith(f"{feature}/"))
    plain = " ".join(report.replace("*", "").replace("`", "").split())
    carried = re.search(r"Carried out in this session:(.*)", report.replace("`", ""))
    carried_ids = set(re.findall(r"T\d+", carried.group(1))) if carried else set()

    committed_files = {f for c in commits for f in c.files}
    lines = []
    touched = sorted(
        f for f in finished_only if f in committed_files or not as_state("committed", f)
    )
    lines.append(
        "ok finished phases untouched"
        if not touched
        else f"FAIL finished phases untouched: {', '.join(touched)}"
    )
    altered = sorted(f for f in left if f in committed_files or not as_state("uncommitted", f))
    lines.append(
        "ok uncommitted changes untouched"
        if not altered
        else f"FAIL uncommitted changes untouched: {', '.join(altered)}"
    )
    # A worker is a main-session Agent call whose brief opens with one of the state's
    # phase headings, whatever model it names: a review's prompt opens otherwise.
    phase_titles = {heading(t) for t, _, _ in all_phases}
    calls = [
        str(block.get("input", {}).get("prompt", ""))
        for event in events
        if event.get("type") == "assistant" and event.get("parent_tool_use_id") is None
        for block in event.get("message", {}).get("content", [])
        if block.get("type") == "tool_use" and block.get("name") == "Agent"
    ]
    opened = [o for o in (heading(c.split("\n", 1)[0]) for c in calls) if o in phase_titles]
    first = opened[0] if opened else "(no worker)"
    if outside:
        lines.append(
            "ok no worker started: core's run"
            if not opened
            else f"FAIL no worker started: {first!r} with {', '.join(outside)} uncommitted"
        )
    else:
        lines.append(
            "ok first brief opens the first unfinished phase"
            if first == heading(title)
            else "FAIL first brief opens the first unfinished phase: "
            f"{first!r}, not {heading(title)!r}"
        )
    done_titles = {heading(t) for t, done, _ in all_phases if done}
    redone = sorted({o for o in opened if o in done_titles})
    lines.append(
        "ok no brief opens a finished phase"
        if not redone
        else f"FAIL no brief opens a finished phase: {', '.join(redone)}"
    )
    # Every task the state names, present and marked: a deleted line is not a done task.
    marked = set(re.findall(r"^- \[[xX]\] (T\d+)", final, re.MULTILINE))
    unmarked = sorted(set(re.findall(r"^- \[[ xX]\] (T\d+)", tasks, re.MULTILINE)) - marked)
    unmarked += sorted(set(re.findall(r"^- \[ \] (T\d+)", final, re.MULTILINE)) - set(unmarked))
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
    if outside:
        unnamed = [f for f in outside if f not in plain]
        lines.append(
            "ok report names the paths outside the feature directory"
            if not unnamed
            else f"FAIL report names the paths outside the feature directory: {', '.join(unnamed)}"
        )
    else:
        want = STARTED.format(n=number.group(1) if number else "?")
        lines.append(
            "ok report names the start"
            if want in plain
            else f"FAIL report names the start: no line {want!r}"
        )
    # A task that changes the feature directory is carried out in this session and
    # left uncommitted: changed in the tree, in no commit, on the Carried out line.
    doc_tasks = {
        task: [p for p in re.findall(r"`([^`]+)`", line) if p.startswith(f"{feature}/")]
        for line in tasks.splitlines()
        if (match := re.match(r"^- \[ \] (T\d+)", line))
        for task in [match.group(1)]
    }
    doc_tasks = {t: ps for t, ps in doc_tasks.items() if ps}
    missed = sorted(
        t
        for t, ps in doc_tasks.items()
        if t not in carried_ids
        or any(
            p in committed_files
            or not (out / "repo" / p).is_file()
            or (out / "repo" / p).read_text() == before(p)
            for p in ps
        )
    )
    named = ", ".join(sorted(doc_tasks)) or "none"
    lines.append(
        f"ok feature-directory tasks carried out in this session: {named}"
        if not missed
        else f"FAIL feature-directory tasks carried out in this session: {', '.join(missed)}"
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
