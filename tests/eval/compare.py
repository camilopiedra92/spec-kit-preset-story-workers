"""The eval's verdict across runs, its difficulty gate, and its spend.

Usage:  compare.py --probes <probes.txt> <run-dir>...
            Three counted runs per arm (`without`, `with`, `fallback`) of one
            fixture: per arm each run, the median and spread; then the gate,
            SC-001, SC-002, SC-003, SC-005, SC-006, SC-007 and SC-008, each
            `ok` or `FAIL` with its numbers. SC-004 is judged outside (CI).
        compare.py --gate <without-run-dir>...
            Three counted `without` runs: `gate open` when one missed a
            held-out test, else `gate closed`.
        compare.py --spent <root> [--fixture <name> --next <arm>...]
            Every try's and probe's cost under <root>, and the total; with
            --next, the estimate for the named arms' sets and its worst case.
Exit:   0 the gate open and every criterion holding (--gate: open; --spent:
        always); 1 otherwise; 2 refused input.

Reads the committed run files only (status, versions.txt, heldout.txt,
suite.txt, usage.json, models.txt, report.txt, attribution.txt) and the
fixture's own files under tests/eval/fixtures/<fixture>/, so committed
results can be re-judged without the scratch repositories. The contract is
specs/002-large-phase-remeasure/contracts/harness.md; the rules are its
data-model.md ("Comparison", "Spend", "Held-out score").
"""

import json
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import usage
from attribution import REPORT_LINE

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"
ARMS = ("without", "with", "fallback")
RUNS_PER_ARM = 3
THRESHOLD = 0.30
# Medians of float costs: 8.4 against 12 is 30% on paper and 29.999…% in floats.
EPSILON = 1e-9
FIELDS = usage.FIELDS
VERSION = re.compile(r"\d+\.\d+\.\d+")
TASK_LINE = re.compile(r"^- \[[ xX]\] (T\d+)\b", re.MULTILINE)


class Refused(Exception):
    pass


def read_versions(run: Path) -> dict[str, str]:
    lines = (run / "versions.txt").read_text().splitlines()
    return {k: v for k, _, v in (line.partition(": ") for line in lines) if k}


@dataclass
class Fixture:
    n: int
    stories: int
    task_ids: list[str]


def at_commit(fixtures: Path, commit: str, path: str) -> str:
    """A fixture file as committed at `commit`: a run is judged by the fixture it
    ran on, which a later hardening changes in the working tree."""
    result = subprocess.run(
        ["git", "-C", str(fixtures), "show", f"{commit}:./{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise Refused(f"{path} at commit {commit!r}: {result.stderr.strip()}")
    return result.stdout


def read_fixture(fixtures: Path, name: str, commit: str) -> Fixture:
    project = f"{name}/project"
    feature = json.loads(at_commit(fixtures, commit, f"{project}/.specify/feature.json"))[
        "feature_directory"
    ]
    spec = at_commit(fixtures, commit, f"{project}/{feature}/spec.md")
    tasks = at_commit(fixtures, commit, f"{project}/{feature}/tasks.md")
    return Fixture(
        int(at_commit(fixtures, commit, f"{name}/heldout/N").strip()),
        len(re.findall(r"^### User Story ", spec, re.MULTILINE)),
        TASK_LINE.findall(tasks),
    )


def task_lines(fixtures: Path, name: str) -> int:
    project = fixtures / name / "project"
    feature = json.loads((project / ".specify/feature.json").read_text())["feature_directory"]
    return len(TASK_LINE.findall((project / feature / "tasks.md").read_text()))


@dataclass
class Run:
    path: Path
    arm: str
    versions: dict[str, str]
    cost: float
    model_costs: dict[str, float]
    passed: int
    suite: int
    usage: dict[str, Any]
    models_txt: str
    report: str
    attribution: str


def read_run(path: Path) -> Run:
    try:
        status = (path / "status").read_text().strip()
        if status != "ok":
            raise Refused(f"{path.name}: status is {status!r}, not 'ok'")
        versions = read_versions(path)
        data = json.loads((path / "usage.json").read_text())
        model_costs = {m: float(v["reported"]["cost"]) for m, v in data["models"].items()}
        passed = re.match(r"passed (\d+)/", (path / "heldout.txt").read_text())
        suite = re.search(r"^exit: (\d+)", (path / "suite.txt").read_text(), re.MULTILINE)
        if not passed or not suite:
            raise Refused(f"{path.name}: heldout.txt or suite.txt unreadable")
        attribution = path / "attribution.txt"
        return Run(
            path,
            versions["arm"],
            versions,
            sum(model_costs.values()),
            model_costs,
            int(passed.group(1)),
            int(suite.group(1)),
            data,
            (path / "models.txt").read_text(),
            (path / "report.txt").read_text(),
            attribution.read_text() if attribution.exists() else "",
        )
    except (OSError, ValueError, KeyError) as error:
        raise Refused(f"{path.name}: {error}") from error


def comparable(runs: list[Run]) -> tuple[str, str]:
    """The runs' fixture and commit; Refused unless they agree in every key but date
    and arm."""
    first = runs[0].versions
    for run in runs[1:]:
        keys = set(first) | set(run.versions)
        differ = sorted(k for k in keys - {"date", "arm"} if first.get(k) != run.versions.get(k))
        if differ:
            raise Refused(f"{run.path.name}: versions differ from {runs[0].path.name}: {differ}")
    return first.get("fixture", ""), first.get("commit", "")


def spread(values: list[float], fmt: str) -> str:
    return (
        f"median {fmt.format(statistics.median(values))} min {fmt.format(min(values))} "
        f"max {fmt.format(max(values))}"
    )


def gate(without: list[Run], n: int) -> tuple[bool, str]:
    scores = ", ".join(f"{r.path.name} {r.passed}/{n}" for r in without)
    return any(r.passed < n for r in without), scores


def usage_holds(data: dict[str, Any]) -> bool:
    for model, totals in data["models"].items():
        reported, transcripts = totals["reported"], totals["transcripts"]
        mine = [p for p in data["parts"] if p["model"] == model]
        # `reported` is modelUsage's (one cache-write total); `transcripts` splits it.
        if any(reported[f] != transcripts[f] for f in ("input", "output", "cache_read")):
            return False
        if reported["cache_write"] != transcripts["cache_write_5m"] + transcripts["cache_write_1h"]:
            return False
        if abs(reported["cost"] - transcripts["cost"]) > usage.TOLERANCE:
            return False
        if any(sum(p[f] for p in mine) != transcripts[f] for f in FIELDS):
            return False
        if abs(sum(p["cost"] for p in mine) - reported["cost"]) > usage.TOLERANCE:
            return False
    return True


def reviews_by_opus(models_txt: str) -> int:
    return sum(
        int(m.group(1))
        for m in re.finditer(r"^agent general-purpose opus \S+ (\d+)$", models_txt, re.MULTILINE)
    )


RANGE = re.compile(r"T(\d+)\s*(?:[–—-]|to)\s*T?(\d+)")


def carried_out(report: str) -> set[str]:
    """The task ids after the report's last `Carried out in this session:` line, a
    range such as T002–T005 standing for every id in it (marks stripped as
    attribution.py strips them)."""
    found = REPORT_LINE.findall(re.sub(r"[*`_]", "", report))
    if not found:
        return set()
    text = found[-1]
    ids = set(re.findall(r"T\d+", text))
    for first, last in RANGE.findall(text):
        width = len(first)
        ids |= {f"T{n:0{width}d}" for n in range(int(first), int(last) + 1)}
    return ids


def verdict(runs: list[Run], probes: str, fx: Fixture) -> tuple[list[str], bool]:
    by_arm = {arm: [r for r in runs if r.arm == arm] for arm in ARMS}
    lines: list[str] = []
    for arm in ARMS:
        for r in by_arm[arm]:
            per_model = " ".join(f"{m} ${c:.4f}" for m, c in sorted(r.model_costs.items()))
            lines.append(
                f"{arm} {r.path.name} ${r.cost:.4f} ({per_model}) held-out {r.passed}/{fx.n} "
                f"suite exit {r.suite}"
            )
        lines.append(f"{arm} {spread([r.cost for r in by_arm[arm]], '${:.4f}')}")
        lines.append(f"{arm} held-out {spread([float(r.passed) for r in by_arm[arm]], '{:g}')}")
    checks: list[tuple[str, bool, str]] = []
    open_, scores = gate(by_arm["without"], fx.n)
    lines.append(f"gate {'open' if open_ else 'closed'}: {scores}")

    cost = {arm: statistics.median(r.cost for r in by_arm[arm]) for arm in ARMS}
    cut = 1 - cost["with"] / cost["without"]
    checks.append(
        (
            "SC-001",
            cut >= THRESHOLD - EPSILON,
            (
                f"with median ${cost['with']:.4f} is {cut:.1%} below without median "
                f"${cost['without']:.4f} (needs {THRESHOLD:.0%})"
            ),
        )
    )
    score = {arm: statistics.median(r.passed for r in by_arm[arm]) for arm in ARMS}
    red = [r.path.name for r in by_arm["with"] if r.suite != 0]
    checks.append(
        (
            "SC-002",
            score["with"] >= score["without"] and not red,
            f"held-out median with {score['with']:g}/{fx.n}, without {score['without']:g}/{fx.n}"
            + (f"; red suite in {', '.join(red)}" if red else ""),
        )
    )
    # Only attribution.py's clauses: the Bash commands it lists after them may say
    # anything, FAILED included.
    clauses = {r.path.name: r.attribution.split("\nmain session's Bash commands:")[0] for r in runs}
    bad = [
        r.path.name
        for r in by_arm["with"]
        if re.search(r"^FAIL ", clauses[r.path.name], re.MULTILINE)
        or not re.search(r"^ok ", clauses[r.path.name], re.MULTILINE)
    ]
    checks.append(("SC-003", not bad, "every clause ok" if not bad else f"failing in {bad}"))
    problems = []
    if score["fallback"] < score["without"]:
        problems.append(f"held-out median {score['fallback']:g} < without {score['without']:g}")
    for r in by_arm["fallback"]:
        if re.search(r"^agent ", r.models_txt, re.MULTILINE):
            problems.append(f"{r.path.name} made an Agent call")
        missing = sorted(set(fx.task_ids) - carried_out(r.report))
        if missing:
            problems.append(f"{r.path.name} report lacks {', '.join(missing)}")
    checks.append(("SC-005", not problems, "; ".join(problems) or "held, no Agent call, all tasks"))
    probe_version = VERSION.search(probes.split("\n", 1)[0])
    failed = [line for line in probes.splitlines() if line.startswith("FAIL")]
    # probes.sh's closing summary: a file cut short has none.
    summary = re.search(r"^probes: \d+ ok, 0 FAIL$", probes, re.MULTILINE)
    off = [
        r.path.name
        for r in runs
        if not probe_version or r.versions.get("claude") != probe_version.group(0)
    ]
    checks.append(
        (
            "SC-006",
            bool(probe_version) and bool(summary) and not failed and not off,
            f"probes on {probe_version.group(0) if probe_version else 'unknown'}"
            + ("" if summary else "; no closing summary line")
            + (f"; failed: {len(failed)}" if failed else "")
            + (f"; other version in {off}" if off else ""),
        )
    )
    few = [r.path.name for r in by_arm["with"] if reviews_by_opus(r.models_txt) < fx.stories]
    checks.append(
        (
            "SC-007",
            not few,
            f"a review per story ({fx.stories})" + (f"; fewer in {few}" if few else ""),
        )
    )
    broken = [r.path.name for r in runs if not usage_holds(r.usage)]
    checks.append(("SC-008", not broken, "reconciled" if not broken else f"broken in {broken}"))
    lines += [f"{key} {'ok' if held else 'FAIL'}: {why}" for key, held, why in checks]
    return lines, open_ and all(held for _, held, _ in checks)


def run_verdict(argv: list[str], fixtures: Path) -> int:
    probes = Path(argv[0]).read_text()
    runs = [read_run(Path(a)) for a in argv[1:]]
    resolved = [r.path.resolve() for r in runs]
    if len(set(resolved)) != len(resolved):
        raise Refused("the same run is given twice")
    for arm in ARMS:
        count = sum(r.arm == arm for r in runs)
        if count != RUNS_PER_ARM:
            raise Refused(f"{arm}: {count} runs, not {RUNS_PER_ARM}")
    fx = read_fixture(fixtures, *comparable(runs))
    lines, holds = verdict(runs, probes, fx)
    print("\n".join(lines))
    return 0 if holds else 1


def run_gate(argv: list[str], fixtures: Path) -> int:
    runs = [read_run(Path(a)) for a in argv]
    if len(runs) != RUNS_PER_ARM or any(r.arm != "without" for r in runs):
        raise Refused(f"--gate takes {RUNS_PER_ARM} counted `without` runs")
    fx = read_fixture(fixtures, *comparable(runs))
    open_, scores = gate(runs, fx.n)
    print(f"gate {'open' if open_ else 'closed'}: {scores}")
    return 0 if open_ else 1


def stream_cost(path: Path) -> float | None:
    """A stream's reported cost, or None when it has no result event."""
    cost = None
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            cost = sum(float(v.get("costUSD", 0)) for v in event.get("modelUsage", {}).values())
    return cost


def run_spent(argv: list[str], fixtures: Path, results: Path) -> int:
    root = Path(argv[0])
    options = argv[1:]
    fixture, arms = "", []
    if options:
        if options[:1] != ["--fixture"] or len(options) < 4 or options[2] != "--next":
            raise Refused("usage: --spent <root> [--fixture <name> --next <arm>...]")
        fixture, arms = options[1], options[3:]
    if not root.is_dir():
        raise Refused(f"{root} is not a directory")
    total = 0.0
    counted: dict[str, list[float]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        # A run's `<arm>-<n>` link points at a try already walked; transcripts
        # are priced with their try.
        if path.is_symlink() or "transcripts" in rel.parts:
            continue
        name = str(rel)
        is_try = path.is_dir() and ((path / "status").exists() or (path / "stream.jsonl").exists())
        if is_try:
            stream = path / "stream.jsonl"
            cost = stream_cost(stream) if stream.exists() else None
            if cost is None and (path / "transcripts").is_dir():
                cost = usage.price_only(path)
            if cost is None:
                print(f"{name} 0 (no cost recorded)")
                continue
            print(f"{name} {cost:.7f}")
            total += cost
            status = path / "status"
            if status.exists() and status.read_text().strip() == "ok":
                versions = read_versions(path)
                if versions.get("fixture") == fixture:
                    counted.setdefault(versions.get("arm", ""), []).append(cost)
        elif path.suffix == ".jsonl" and not (
            (path.parent / "status").exists() or path.name == "stream.jsonl"
        ):
            cost = stream_cost(path)
            print(f"{name} {cost:.7f}" if cost is not None else f"{name} 0 (no cost recorded)")
            total += cost or 0.0
    estimates = []
    for arm in arms:
        if arm in counted:
            per_run, label = max(counted[arm]), ""
        elif counted:
            per_run, label = 2 * max(c for cs in counted.values() for c in cs), " (provisional)"
        else:
            base = (results / "2026-10-14/without/usage.txt").read_text()
            found = re.search(r"^sum (\S+)$", base, re.MULTILINE)
            if not found:
                raise Refused("001's without usage.txt has no sum line")
            ratio = task_lines(fixtures, fixture) / task_lines(fixtures, "wordstats")
            per_run, label = float(found.group(1)) * ratio, " (unmeasured)"
        estimates.append(RUNS_PER_ARM * per_run)
        print(f"estimate {arm} {RUNS_PER_ARM * per_run:.7f}{label}")
    if arms:
        print(f"estimate total {sum(estimates):.7f} worst case {3 * sum(estimates):.7f}")
    print(f"spent {total:.7f}" if total else "spent 0")
    return 0


def main(argv: list[str], fixtures: Path = FIXTURES, results: Path = RESULTS) -> int:
    if argv == ["--help"]:
        print(__doc__)
        return 0
    try:
        if argv[:1] == ["--probes"] and len(argv) > 2:
            return run_verdict(argv[1:], fixtures)
        if argv[:1] == ["--gate"]:
            return run_gate(argv[1:], fixtures)
        if argv[:1] == ["--spent"] and len(argv) > 1:
            return run_spent(argv[1:], fixtures, results)
        raise Refused(__doc__.split("Exit:")[0].strip() if __doc__ else "usage")
    except (Refused, OSError, ValueError, KeyError) as error:
        print(f"compare.py: refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
