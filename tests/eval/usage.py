"""A run's usage, reconciled with what Claude Code reported, then attributed.

Usage:  usage.py [--price-only] <out-dir>
Reads   <out-dir>/stream.jsonl (the `result` event's `modelUsage`, the
        `rate_limit_event`s), <out-dir>/transcripts/ (the main session's
        <session_id>.jsonl and subagents/agent-*.{jsonl,meta.json}, copied
        by run.sh) and versions.txt (`arm`, `fixture`, `commit`); for `with`,
        the phase headings of tests/eval/fixtures/<fixture>/project/'s feature
        tasks.md as committed at that commit.
Writes  usage.json and usage.txt when the transcripts reconcile with
        `modelUsage`: per model and token type equal, priced cost within
        $0.000001 of `costUSD`. Otherwise writes nothing and prints
        `unreconciled: <reason>[; ...]`.
Exit:   0 reconciled; 1 unreconciled; 2 a fault in this script.
        --price-only prints `spent <usd>`, the transcripts' cost at the price
        table (for a try whose stream has no `result` event), and exits 0.

The transcript format is Claude Code's internal one, observed to reconcile
exactly on 2026-10-14 (research.md R1); the check on every run is what makes
relying on it safe. Spans of the `with` main session are spec FR-013.
"""

import json
import re
import subprocess
import sys
import traceback
from dataclasses import astuple, dataclass, field
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"
TOLERANCE = 1e-6
# USD per million tokens: input, output, cache read, 5-minute write, 1-hour write.
# Source: https://platform.claude.com/docs/en/about-claude/pricing, read 2026-10-14.
# A price change shows as an unreconciled run, never as a silently wrong split.
PRICES: dict[str, tuple[float, float, float, float, float]] = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0, 8.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10, 2.5, 4.0),
}
FIELDS = ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h")


@dataclass
class Tokens:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0

    def __add__(self, other: "Tokens") -> "Tokens":
        return Tokens(*(a + b for a, b in zip(astuple(self), astuple(other), strict=True)))

    def as_dict(self) -> dict[str, int]:
        return dict(zip(FIELDS, astuple(self), strict=True))


def price(model: str, t: Tokens) -> float:
    """The tokens' cost at the list price; KeyError for a model with no price."""
    rates = PRICES[model]
    return float(sum(n * r for n, r in zip(astuple(t), rates, strict=True))) / 1e6


class Unreconciled(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass
class Turn:
    """One assistant message: its transcript entries merged by `message.id`."""

    model: str
    tokens: Tokens
    calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Transcript:
    turns: list[Turn]
    # tool_use id -> is_error, from the user entries' tool_result blocks.
    results: dict[str, bool]


def read_jsonl(path: Path, tolerant: bool = False) -> list[dict[str, Any]]:
    """The file's JSON lines; Unreconciled on a bad one, or skipped when tolerant
    (a try killed at its deadline can leave a partial last line)."""
    entries = []
    try:
        lines = path.read_text().splitlines()
    except OSError as error:
        raise Unreconciled([f"unreadable {path.name}"]) from error
    for line in lines:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except ValueError as error:
            if not tolerant:
                raise Unreconciled([f"unreadable {path.name}"]) from error
    return entries


def usage_tokens(u: dict[str, Any]) -> Tokens:
    split = u.get("cache_creation") or {}
    return Tokens(
        u.get("input_tokens", 0),
        u.get("output_tokens", 0),
        u.get("cache_read_input_tokens", 0),
        split.get("ephemeral_5m_input_tokens", 0),
        split.get("ephemeral_1h_input_tokens", 0),
    )


def parse_transcript(path: Path, tolerant: bool = False) -> Transcript:
    turns: dict[str, Turn] = {}
    results: dict[str, bool] = {}
    for entry in read_jsonl(path, tolerant):
        message = entry.get("message") or {}
        content = message.get("content")
        blocks = content if isinstance(content, list) else []
        if entry.get("type") == "assistant" and message.get("usage"):
            tokens = usage_tokens(message["usage"])
            if tokens == Tokens():
                # Claude Code's synthetic messages (API errors, model "<synthetic>")
                # carry zero usage: no request was billed, so they are no turn.
                continue
            msg_id = message.get("id", "")
            # Each entry repeats the message's usage; the last one counts (research R1 2).
            turn = turns.setdefault(msg_id, Turn(message.get("model", ""), Tokens()))
            turn.tokens = tokens
            turn.calls += [b for b in blocks if b.get("type") == "tool_use"]
        elif entry.get("type") == "user":
            for b in blocks:
                if b.get("type") == "tool_result":
                    results[b.get("tool_use_id", "")] = bool(b.get("is_error"))
    return Transcript(list(turns.values()), results)


def heading(line: str) -> str:
    """A phase heading's text, heading and emphasis marks dropped (as attribution.py)."""
    return line.strip().lstrip("#*").rstrip("*").strip()


def fixture_file(fixtures: Path, commit: str, path: str) -> str:
    """A fixture file as committed at `commit` (`git show`): a run is read against
    the fixture it measured, which a later hardening changes in the tree.
    ValueError when the repository lacks the commit or the file."""
    result = subprocess.run(
        ["git", "-C", str(fixtures), "show", f"{commit}:./{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"{path} at commit {commit!r}: {result.stderr.strip()}")
    return result.stdout


def phase_headings(fixtures: Path, fixture: str, commit: str) -> dict[int, str]:
    project = f"{fixture}/project"
    feature = json.loads(fixture_file(fixtures, commit, f"{project}/.specify/feature.json"))[
        "feature_directory"
    ]
    found: dict[int, str] = {}
    for line in fixture_file(fixtures, commit, f"{project}/{feature}/tasks.md").splitlines():
        match = re.match(r"## Phase (\d+)\b", line)
        if match:
            found[int(match.group(1))] = heading(line)
    return found


def brief_phase(prompt: str, headings: dict[int, str]) -> int | None:
    first = heading(prompt.split("\n", 1)[0]) if prompt else ""
    return next((n for n, h in headings.items() if h == first), None)


def spans(main: Transcript, headings: dict[int, str]) -> list[tuple[str, int | None]]:
    """Each main-session turn's (part, phase), as spec FR-013 defines them."""
    starts: dict[int, int] = {}
    markings: dict[int, int] = {}
    for i, turn in enumerate(main.turns):
        for call in turn.calls:
            input_ = call.get("input") or {}
            if call.get("name") == "Agent" and input_.get("model") == "sonnet":
                n = brief_phase(str(input_.get("prompt", "")), headings)
                if n is not None:
                    starts.setdefault(n, i)
            if call.get("name") == "Bash" and not main.results.get(call.get("id", ""), True):
                command = str(input_.get("command", ""))
                if re.search(r"\bgit\b(\s+-C\s+\S+)?\s+commit\b", command):
                    for n in headings:
                        if re.search(rf"tasks: mark phase {n}\b", command):
                            markings.setdefault(n, i)
    order = sorted(headings)
    broken = None
    for k, n in enumerate(order):
        nxt = order[k + 1] if k + 1 < len(order) else None
        if (
            n not in starts
            or n not in markings
            or starts[n] > markings[n]
            or (nxt is not None and nxt in starts and markings[n] >= starts[nxt])
        ):
            broken = k
            break
    labels: list[tuple[str, int | None]] = []
    good = order if broken is None else order[:broken]
    last = markings[good[-1]] if good else -1
    for i in range(len(main.turns)):
        if not good:
            labels.append(("unattributed", None))
        elif i < starts[good[0]]:
            labels.append(("before", None))
        elif i <= last:
            labels.append(("phase", next(n for n in good if i <= markings[n])))
        else:
            labels.append(("after", None) if broken is None else ("unattributed", None))
    return labels


@dataclass
class Run:
    reported: dict[str, dict[str, Any]]
    five_hour: tuple[Any, Any]
    arm: str
    fixture: str
    commit: str
    session: str


def five_hour(event: dict[str, Any]) -> Any:
    """A rate_limit_event's five-hour utilization, None when the event lacks it."""
    windows = (event.get("rate_limit_info") or {}).get("unifiedWindows") or {}
    return (windows.get("five_hour") or {}).get("utilization")


def read_run(out: Path) -> Run:
    events = read_jsonl(out / "stream.jsonl")
    results = [e for e in events if e.get("type") == "result"]
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    windows = [
        window
        for e in events
        if e.get("type") == "rate_limit_event" and (window := five_hour(e)) is not None
    ]
    versions = {
        key: value
        for key, _, value in (
            line.partition(": ") for line in (out / "versions.txt").read_text().splitlines()
        )
    }
    return Run(
        results[-1].get("modelUsage", {}) if results else {},
        (windows[0], windows[-1]) if windows else ("-", "-"),
        versions.get("arm", ""),
        versions.get("fixture", ""),
        versions.get("commit", ""),
        str(init.get("session_id", "")),
    )


@dataclass
class Sub:
    meta: dict[str, Any]
    transcript: Transcript


def read_transcripts(out: Path, session: str) -> tuple[Transcript, list[Sub]]:
    main = out / "transcripts" / f"{session}.jsonl"
    if not session or not main.is_file():
        raise Unreconciled(["no transcript"])
    subs = []
    for path in sorted((out / "transcripts/subagents").glob("agent-*.jsonl")):
        meta_path = path.with_name(path.name.removesuffix(".jsonl") + ".meta.json")
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, ValueError) as error:
            raise Unreconciled([f"unreadable {meta_path.name}"]) from error
        subs.append(Sub(meta, parse_transcript(path)))
    return parse_transcript(main), subs


def reconcile(run: Run, transcripts: list[Transcript]) -> dict[str, dict[str, Any]]:
    """Per model, the transcripts' sums beside the reported ones; Unreconciled on a gap."""
    summed: dict[str, Tokens] = {}
    for t in transcripts:
        for turn in t.turns:
            summed[turn.model] = summed.get(turn.model, Tokens()) + turn.tokens
    reasons: list[str] = []
    models: dict[str, dict[str, Any]] = {}
    for model in sorted(set(summed) | set(run.reported)):
        mine = summed.get(model, Tokens())
        theirs = run.reported.get(model, {})
        pairs = {
            "input": (mine.input, theirs.get("inputTokens", 0)),
            "output": (mine.output, theirs.get("outputTokens", 0)),
            "cache_read": (mine.cache_read, theirs.get("cacheReadInputTokens", 0)),
            "cache_write": (
                mine.cache_write_5m + mine.cache_write_1h,
                theirs.get("cacheCreationInputTokens", 0),
            ),
        }
        reasons += [
            f"{model} {name} transcript={a} reported={b}"
            for name, (a, b) in pairs.items()
            if a != b
        ]
        reported_cost = float(theirs.get("costUSD", 0.0))
        if mine == Tokens() and not reported_cost and all(b == 0 for _, b in pairs.values()):
            continue  # a model named with nothing on it: nothing to price or split
        if model not in PRICES:
            reasons.append(f"{model} price unknown")
            continue
        priced = price(model, mine)
        if abs(priced - reported_cost) > TOLERANCE:
            reasons.append(f"{model} cost priced={priced:.7f} reported={reported_cost:.7f}")
        models[model] = {
            # modelUsage's own numbers, so the committed file shows both sides of the
            # check; it gives one cache-write total, the transcripts give the split.
            "reported": {
                "input": theirs.get("inputTokens", 0),
                "output": theirs.get("outputTokens", 0),
                "cache_read": theirs.get("cacheReadInputTokens", 0),
                "cache_write": theirs.get("cacheCreationInputTokens", 0),
                "cost": reported_cost,
            },
            "transcripts": {**mine.as_dict(), "cost": priced},
        }
    if reasons:
        raise Unreconciled(reasons)
    return models


def attribute(run: Run, main: Transcript, subs: list[Sub], fixtures: Path) -> list[dict[str, Any]]:
    totals: dict[tuple[str, int | None, str], Tokens] = {}
    counts: dict[tuple[str, int | None, str], int] = {}

    def add(part: str, phase: int | None, model: str, t: Tokens) -> None:
        key = (part, phase, model)
        totals[key] = totals.get(key, Tokens()) + t
        counts.setdefault(key, 0)

    if run.arm == "with":
        headings = phase_headings(fixtures, run.fixture, run.commit)
        labels = spans(main, headings)
    else:
        headings, labels = {}, [("main", None)] * len(main.turns)
    calls: dict[str, tuple[int, dict[str, Any]]] = {}
    for i, (turn, (part, phase)) in enumerate(zip(main.turns, labels, strict=True)):
        add(part, phase, turn.model, turn.tokens)
        for call in turn.calls:
            calls[call.get("id", "")] = (i, call.get("input") or {})
    for sub in subs:
        model = str(sub.meta.get("model", ""))
        found = calls.get(str(sub.meta.get("toolUseId", "")))
        if model == "sonnet":
            part = "worker"
            phase = brief_phase(str(found[1].get("prompt", "")), headings) if found else None
        else:
            part = "review" if sub.meta.get("agentType") == "general-purpose" else "other"
            phase = None
            if found and labels[found[0]][0] == "phase":
                phase = labels[found[0]][1]
        for turn in sub.transcript.turns:
            add(part, phase, turn.model, turn.tokens)
        for model in {turn.model for turn in sub.transcript.turns}:
            counts[(part, phase, model)] += 1
    order = ["main", "before", "phase", "after", "unattributed", "worker", "review", "other"]
    return [
        {
            "part": part,
            "phase": phase,
            "model": model,
            "subagents": counts[(part, phase, model)],
            **t.as_dict(),
            "cost": price(model, t),
        }
        # Session order: the main session's parts as they happened, then subagents.
        for (part, phase, model), t in sorted(
            totals.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1] or 0, kv[0][2])
        )
    ]


def render(run: Run, models: dict[str, dict[str, Any]], parts: list[dict[str, Any]]) -> str:
    def counts(d: dict[str, Any]) -> str:
        return " ".join(f"{f} {d[f]}" for f in FIELDS)

    lines = [
        f"{m} cost {v['reported']['cost']:.7f} {counts(v['transcripts'])}"
        for m, v in models.items()
    ]
    lines.append(f"sum {sum(v['reported']['cost'] for v in models.values()):.7f}")
    lines.append(f"five_hour {run.five_hour[0]} {run.five_hour[1]}")
    lines.append("reconciled yes")
    lines += [
        f"part {p['part']} phase {p['phase'] if p['phase'] is not None else '-'} "
        f"{p['model']} cost {p['cost']:.7f} {counts(p)}"
        for p in parts
    ]
    return "\n".join(lines) + "\n"


def price_only(out: Path) -> float:
    total = 0.0
    tr = out / "transcripts"
    if not tr.is_dir():
        return total
    for path in [*tr.glob("*.jsonl"), *(tr / "subagents").glob("agent-*.jsonl")]:
        for turn in parse_transcript(path, tolerant=True).turns:
            total += price(turn.model, turn.tokens) if turn.model in PRICES else 0.0
    return total


def main(argv: list[str], fixtures: Path = FIXTURES) -> int:
    try:
        if argv[:1] == ["--price-only"]:
            spent = price_only(Path(argv[1]))
            print(f"spent {spent:.7f}" if spent else "spent 0")
            return 0
        out = Path(argv[0])
        try:
            run = read_run(out)
            main_t, subs = read_transcripts(out, run.session)
            models = reconcile(run, [main_t, *(s.transcript for s in subs)])
        except Unreconciled as error:
            print(f"unreconciled: {error}")
            return 1
        parts = attribute(run, main_t, subs, fixtures)
        (out / "usage.json").write_text(
            json.dumps({"models": models, "parts": parts}, indent=2) + "\n"
        )
        (out / "usage.txt").write_text(render(run, models, parts))
        return 0
    except Exception:  # noqa: BLE001 - every other failure is this script's own fault
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
