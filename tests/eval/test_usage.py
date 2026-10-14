"""usage.py: a run's usage reconciled with what Claude Code reported, then attributed.

Each test writes a synthetic run directory in the shapes Claude Code 2.1.299
writes (research R1): a stream with `init` and `result` events, the main
transcript with one entry per content block (an assistant message spans
several entries sharing `message.id`), and subagent transcripts with their
meta files. The reported `modelUsage` is computed from the same entries at
the list prices, so a run reconciles unless a test breaks it on purpose.
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import usage

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
SESSION = "sess-1"
# Per million tokens: input, output, cache read, 5-minute write, 1-hour write
# (platform.claude.com/docs/en/about-claude/pricing, read 2026-10-14).
PRICES = {OPUS: (4, 20, 0.20, 5, 8), SONNET: (2, 10, 0.10, 2.5, 4)}

TASKS = """# Tasks

## Phase 1: Setup

- [ ] T001 a

## Phase 2: User Story 1 - One (Priority: P1)

- [ ] T002 [US1] b

## Phase 3: User Story 2 - Two (Priority: P2)

- [ ] T003 [US2] c

## Phase 4: User Story 3 - Three (Priority: P3)

- [ ] T004 [US3] d
"""
HEADINGS = [line for line in TASKS.splitlines() if line.startswith("## Phase")]


def tokens(n: int) -> dict[str, Any]:
    """A usage block whose fields differ, so a field mixed up shows."""
    return {
        "input_tokens": n,
        "output_tokens": 10 * n,
        "cache_read_input_tokens": 100 * n,
        "cache_creation_input_tokens": 3 * n,
        "cache_creation": {"ephemeral_5m_input_tokens": n, "ephemeral_1h_input_tokens": 2 * n},
    }


def cost(model: str, u: dict[str, Any]) -> float:
    # A model with no list price costs nothing here; usage.py must refuse to guess.
    p_in, p_out, p_read, p_5m, p_1h = PRICES.get(model, (0, 0, 0, 0, 0))
    c = u["cache_creation"]
    return (
        float(
            u["input_tokens"] * p_in
            + u["output_tokens"] * p_out
            + u["cache_read_input_tokens"] * p_read
            + c["ephemeral_5m_input_tokens"] * p_5m
            + c["ephemeral_1h_input_tokens"] * p_1h
        )
        / 1e6
    )


@dataclass
class Transcript:
    """Assistant messages in order; each becomes one entry per content block."""

    model: str
    entries: list[dict[str, Any]] = field(default_factory=list)
    messages: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    _n: int = 0

    def turn(self, *blocks: dict[str, Any], weight: int = 1) -> str:
        self._n += 1
        msg_id = f"msg_{self.model[-3:]}_{self._n}"
        u = tokens(weight)
        content = list(blocks) or [{"type": "text", "text": "thinking aloud"}]
        for block in content:
            # Each entry repeats the message's usage; it counts once (research R1 2).
            self.entries.append(
                {
                    "type": "assistant",
                    "message": {"id": msg_id, "model": self.model, "usage": u, "content": [block]},
                }
            )
        self.messages.append((msg_id, u))
        return msg_id

    def result(self, tool_id: str, is_error: bool = False) -> None:
        block = {"type": "tool_result", "tool_use_id": tool_id, "is_error": is_error}
        self.entries.append({"type": "user", "message": {"content": [block]}})


def lines(entries: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(e) + "\n" for e in entries)


def agent(tool_id: str, prompt: str, model: str | None = None) -> dict[str, Any]:
    input_: dict[str, Any] = {"subagent_type": "general-purpose", "prompt": prompt}
    if model:
        input_["model"] = model
    return {"type": "tool_use", "id": tool_id, "name": "Agent", "input": input_}


def bash(tool_id: str, command: str) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": command}}


def mark(n: int) -> str:
    return f'git add tasks.md && git commit -q -m "fixture: tasks: mark phase {n}"'


def brief(n: int) -> str:
    return f"{HEADINGS[n - 1]}\n\nYou are implementing one phase."


@dataclass
class Sub:
    tool_id: str
    meta: dict[str, Any]
    transcript: Transcript


@dataclass
class Run:
    arm: str = "with"
    main: Transcript = field(default_factory=lambda: Transcript(OPUS))
    subs: list[Sub] = field(default_factory=list)

    def sub(
        self, tool_id: str, runs_on: str, agent_type: str = "general-purpose", **meta: Any
    ) -> Sub:
        meta = {"agentType": agent_type, "toolUseId": tool_id, **meta}
        if runs_on == SONNET:
            meta.setdefault("model", "sonnet")
        s = Sub(tool_id, meta, Transcript(runs_on))
        s.transcript.turn(weight=5)
        self.subs.append(s)
        return s

    def reported(self) -> dict[str, dict[str, Any]]:
        totals: dict[str, dict[str, Any]] = {}
        for t in [self.main, *(s.transcript for s in self.subs)]:
            for _, u in t.messages:
                m = totals.setdefault(
                    t.model,
                    {
                        "inputTokens": 0,
                        "outputTokens": 0,
                        "cacheReadInputTokens": 0,
                        "cacheCreationInputTokens": 0,
                        "costUSD": 0.0,
                    },
                )
                m["inputTokens"] += u["input_tokens"]
                m["outputTokens"] += u["output_tokens"]
                m["cacheReadInputTokens"] += u["cache_read_input_tokens"]
                m["cacheCreationInputTokens"] += u["cache_creation_input_tokens"]
                m["costUSD"] += cost(t.model, u)
        return totals

    def write(self, root: Path, reported: dict[str, Any] | None = None) -> Path:
        out = root / "run"
        fixtures = root / "fixtures"
        feature = fixtures / "fx/project/specs/001-fx"
        feature.mkdir(parents=True)
        (fixtures / "fx/project/.specify").mkdir()
        (fixtures / "fx/project/.specify/feature.json").write_text(
            '{"feature_directory": "specs/001-fx"}\n'
        )
        (feature / "tasks.md").write_text(TASKS)
        tr = out / "transcripts"
        (tr / "subagents").mkdir(parents=True)
        (tr / f"{SESSION}.jsonl").write_text(lines(self.main.entries))
        for s in self.subs:
            name = f"agent-{s.tool_id}"
            (tr / f"subagents/{name}.jsonl").write_text(lines(s.transcript.entries))
            (tr / f"subagents/{name}.meta.json").write_text(json.dumps(s.meta))
        events: list[dict[str, Any]] = [
            {"type": "system", "subtype": "init", "session_id": SESSION},
            {
                "type": "rate_limit_event",
                "rate_limit_info": {"unifiedWindows": {"five_hour": {"utilization": 0.1}}},
            },
            {"type": "result", "modelUsage": reported or self.reported()},
            {
                "type": "rate_limit_event",
                "rate_limit_info": {"unifiedWindows": {"five_hour": {"utilization": 0.12}}},
            },
        ]
        (out / "stream.jsonl").write_text(lines(events))
        # The fixture committed: a run's phases are read at the commit it measured.
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "add", "fixtures"], check=True)
        subprocess.run([*git, "commit", "-qm", "fixture"], check=True)
        sha = subprocess.run(
            [*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        (out / "versions.txt").write_text(f"commit: {sha}\nfixture: fx\narm: {self.arm}\n")
        return out


def attribute(run: Run, tmp_path: Path, **kw: Any) -> tuple[int, Path]:
    out = run.write(tmp_path, **kw)
    return usage.main([str(out)], fixtures=tmp_path / "fixtures"), out


def parts(out: Path) -> list[dict[str, Any]]:
    data: dict[str, Any] = json.loads((out / "usage.json").read_text())
    result: list[dict[str, Any]] = data["parts"]
    return result


def by_part(out: Path) -> dict[tuple[str, int | None, str], dict[str, Any]]:
    return {(p["part"], p["phase"], p["model"]): p for p in parts(out)}


def main_turn_weights(out: Path) -> dict[tuple[str, int | None], int]:
    """Each main part's input tokens: with every turn weighted by a distinct number."""
    return {(p["part"], p["phase"]): p["input"] for p in parts(out) if p["model"] == OPUS}


def well_formed(run: Run, phases: int = 4) -> None:
    """before, then per phase: brief, worker, marking; then after."""
    run.main.turn(weight=1)  # before
    for n in range(1, phases + 1):
        run.main.turn(weight=10 * n)  # preparing the brief
        run.main.turn(agent(f"w{n}", brief(n), "sonnet"), weight=100 * n)
        run.main.result(f"w{n}")
        run.sub(f"w{n}", SONNET)
        run.main.turn(bash(f"m{n}", mark(n)), weight=1000 * n)
        run.main.result(f"m{n}")
    run.main.turn(weight=7)  # after


# Reconciliation.


def test_a_reconciled_run_writes_both_files(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    code, out = attribute(run, tmp_path)
    assert code == 0
    text = (out / "usage.txt").read_text()
    reported = run.reported()
    opus = reported[OPUS]
    assert (
        f"{OPUS} cost {opus['costUSD']:.7f} input {opus['inputTokens']} "
        f"output {opus['outputTokens']} cache_read {opus['cacheReadInputTokens']} "
    ) in text
    assert f"sum {opus['costUSD'] + reported[SONNET]['costUSD']:.7f}" in text
    assert "five_hour 0.1 0.12" in text
    assert "reconciled yes" in text
    assert "\npart phase phase 2 claude-opus-5-5 cost " in text  # contract: part <part> phase <n>
    data = json.loads((out / "usage.json").read_text())
    # `reported` is modelUsage's own numbers: one cache-write total, no split.
    assert data["models"][OPUS]["reported"] == {
        "input": opus["inputTokens"],
        "output": opus["outputTokens"],
        "cache_read": opus["cacheReadInputTokens"],
        "cache_write": opus["cacheCreationInputTokens"],
        "cost": opus["costUSD"],
    }
    assert data["models"][OPUS]["transcripts"]["cache_write_1h"] == 2 * opus["inputTokens"]


def test_parts_sum_to_the_totals(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    run.sub("r1", OPUS, model="opus")
    _, out = attribute(run, tmp_path)
    data = json.loads((out / "usage.json").read_text())
    for model, totals in data["models"].items():
        mine = [p for p in data["parts"] if p["model"] == model]
        for key in ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h"):
            assert sum(p[key] for p in mine) == totals["transcripts"][key], (model, key)
        assert abs(sum(p["cost"] for p in mine) - totals["reported"]["cost"]) <= 1e-6


def test_entries_of_one_message_count_once(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn(bash("a", "ls"), bash("b", "pwd"), {"type": "text", "text": "x"}, weight=3)
    code, out = attribute(run, tmp_path)
    assert code == 0
    assert main_turn_weights(out) == {("main", None): 3}


@pytest.mark.parametrize(
    ("model", "tokens_", "expected"),
    [
        # 001's four runs, from their transcripts (research R1 4): input, output,
        # cache read, 5-minute write, 1-hour write.
        (OPUS, (40, 8689, 475794, 27156, 24207), 0.5985348),
        (OPUS, (46, 13490, 611585, 20391, 32369), 0.753208),
        (SONNET, (26, 5875, 238598, 59752, 0), 0.2320418),
        (OPUS, (28, 6464, 400884, 0, 24304), 0.4040008),
    ],
)
def test_the_price_table_reproduces_001s_costs(
    model: str, tokens_: tuple[int, int, int, int, int], expected: float
) -> None:
    assert abs(usage.price(model, usage.Tokens(*tokens_)) - expected) <= 1e-7


def test_no_transcript_is_unreconciled(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    out = run.write(tmp_path)
    (out / f"transcripts/{SESSION}.jsonl").unlink()
    code = usage.main([str(out)], fixtures=tmp_path / "fixtures")
    assert code == 1
    assert not (out / "usage.txt").exists()
    assert not (out / "usage.json").exists()


@pytest.mark.parametrize(
    "field_", ["inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"]
)
def test_a_token_count_off_by_one_is_unreconciled(
    tmp_path: Path, field_: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Run(arm="without")
    run.main.turn()
    reported = run.reported()
    reported[OPUS][field_] += 1
    code, out = attribute(run, tmp_path, reported=reported)
    assert code == 1
    assert "unreconciled:" in capsys.readouterr().out
    assert not (out / "usage.json").exists()


def test_cost_beyond_the_tolerance_is_unreconciled(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    reported = run.reported()
    reported[OPUS]["costUSD"] += 2e-6
    code, _ = attribute(run, tmp_path, reported=reported)
    assert code == 1


def test_cost_within_the_tolerance_reconciles(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    reported = run.reported()
    reported[OPUS]["costUSD"] += 5e-7
    code, _ = attribute(run, tmp_path, reported=reported)
    assert code == 0


def test_a_model_with_no_price_is_unreconciled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Run(arm="without")
    run.main.turn()
    run.sub("x", "claude-mystery-9", agent_type="Explore")
    reported = run.reported()
    reported["claude-mystery-9"]["costUSD"] = 0.0
    code, _ = attribute(run, tmp_path, reported=reported)
    assert code == 1
    assert "claude-mystery-9 price unknown" in capsys.readouterr().out


def test_a_model_reported_but_not_in_the_transcripts_is_unreconciled(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    reported = run.reported()
    reported[SONNET] = dict(reported[OPUS])
    code, _ = attribute(run, tmp_path, reported=reported)
    assert code == 1


def test_an_unparsable_transcript_line_is_unreconciled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Run(arm="without")
    run.main.turn()
    out = run.write(tmp_path)
    with (out / f"transcripts/{SESSION}.jsonl").open("a") as f:
        f.write("{not json\n")
    code = usage.main([str(out)], fixtures=tmp_path / "fixtures")
    assert code == 1
    assert "unreadable" in capsys.readouterr().out


def test_an_internal_fault_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = Run(arm="without")
    run.main.turn()
    out = run.write(tmp_path)

    def boom(*_: Any) -> None:
        raise RuntimeError("bug")

    monkeypatch.setattr(usage, "reconcile", boom)
    assert usage.main([str(out)], fixtures=tmp_path / "fixtures") == 2


# Subagent parts.


@pytest.mark.parametrize(
    ("model", "agent_type", "meta_model", "part"),
    [
        (SONNET, "general-purpose", "sonnet", "worker"),
        (OPUS, "general-purpose", "opus", "review"),
        (OPUS, "general-purpose", "inherit", "review"),
        (OPUS, "general-purpose", None, "review"),
        (OPUS, "Explore", None, "other"),
    ],
)
def test_subagents_are_classified_by_their_meta(
    tmp_path: Path, model: str, agent_type: str, meta_model: str | None, part: str
) -> None:
    run = Run(arm="without")
    run.main.turn(agent("s1", "Review it", meta_model))
    run.main.result("s1")
    s = run.sub("s1", model, agent_type=agent_type)
    s.meta.pop("model", None)
    if meta_model:
        s.meta["model"] = meta_model
    _, out = attribute(run, tmp_path)
    assert {p["part"] for p in parts(out) if p["part"] != "main"} == {part}


def test_without_and_fallback_main_is_one_part(tmp_path: Path) -> None:
    run = Run(arm="fallback")
    well_formed(run)  # markings and briefs in the stream do not split a non-`with` run
    run.subs.clear()
    _, out = attribute(run, tmp_path)
    assert {(p["part"], p["phase"]) for p in parts(out)} == {("main", None)}


# The `with` main session's spans (spec FR-013).


def test_a_well_formed_session(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {
        # Phase 1 starts at its worker call, so preparing its brief is `before`;
        # from phase 2 on, preparing a brief belongs to its phase.
        ("before", None): 1 + 10,
        ("phase", 1): 100 + 1000,
        ("phase", 2): 20 + 200 + 2000,
        ("phase", 3): 30 + 300 + 3000,
        ("phase", 4): 40 + 400 + 4000,
        ("after", None): 7,
    }


def test_workers_take_the_phase_their_brief_names(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    _, out = attribute(run, tmp_path)
    workers = {p["phase"] for p in parts(out) if p["part"] == "worker"}
    assert workers == {1, 2, 3, 4}


def test_a_review_takes_the_phase_whose_span_holds_its_call(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=100)
    run.main.result("w1")
    run.sub("w1", SONNET)
    run.main.turn(agent("r1", "Review phase 1", "opus"), weight=200)
    run.main.result("r1")
    run.sub("r1", OPUS, model="opus")
    run.main.turn(bash("m1", mark(1)), weight=1000)
    run.main.result("m1")
    for n in (2, 3, 4):
        run.main.turn(agent(f"w{n}", brief(n), "sonnet"), weight=1)
        run.main.result(f"w{n}")
        run.main.turn(bash(f"m{n}", mark(n)), weight=1)
        run.main.result(f"m{n}")
    run.main.turn(agent("r9", "Final review", "opus"), weight=5)
    run.main.result("r9")
    run.sub("r9", OPUS, model="opus")
    _, out = attribute(run, tmp_path)
    reviews = sorted((p["phase"] or 0) for p in parts(out) if p["part"] == "review")
    assert reviews == [0, 1]  # phase 1, and `null` for the one in `after`


def test_a_phase_never_marked_breaks_from_there(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1", mark(1)), weight=2)
    run.main.result("m1")
    run.main.turn(agent("w2", brief(2), "sonnet"), weight=4)
    run.main.result("w2")
    run.main.turn(weight=8)  # phase 2 never marked
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("phase", 1): 3, ("unattributed", None): 12}


def test_a_marking_before_its_start_breaks(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1", mark(1)), weight=2)
    run.main.result("m1")
    run.main.turn(bash("m2", mark(2)), weight=4)
    run.main.result("m2")
    run.main.turn(agent("w2", brief(2), "sonnet"), weight=8)
    run.main.result("w2")
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("phase", 1): 3, ("unattributed", None): 12}


def test_the_next_phase_handed_off_before_this_one_is_marked_breaks_here(
    tmp_path: Path,
) -> None:
    run = Run()
    run.main.turn(weight=1)  # before
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=2)
    run.main.result("w1")
    run.main.turn(agent("w2", brief(2), "sonnet"), weight=4)  # before phase 1's marking
    run.main.result("w2")
    run.sub("w2", SONNET)
    run.main.turn(bash("m1", mark(1)), weight=8)
    run.main.result("m1")
    _, out = attribute(run, tmp_path)
    # Phase 1 breaks: every turn, `before` included, is unattributed.
    assert main_turn_weights(out) == {("unattributed", None): 15}
    # A worker still takes the phase its brief names.
    assert {p["phase"] for p in parts(out) if p["part"] == "worker"} == {2}


def test_two_markings_in_one_call_break_at_the_second(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1", mark(1)), weight=2)
    run.main.result("m1")
    run.main.turn(agent("w2", brief(2), "sonnet"), weight=4)
    run.main.result("w2")
    run.main.turn(bash("m23", mark(2) + " && " + mark(3)), weight=8)
    run.main.result("m23")
    run.main.turn(agent("w3", brief(3), "sonnet"), weight=16)
    run.main.result("w3")
    _, out = attribute(run, tmp_path)
    # marking₂ and marking₃ are one turn, before start₃: phase 2 holds
    # (marking₂ < start₃), phase 3 breaks (start₃ > marking₃).
    assert main_turn_weights(out) == {
        ("phase", 1): 3,
        ("phase", 2): 12,
        ("unattributed", None): 16,
    }


def test_a_failed_marking_then_a_successful_one(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1a", mark(1)), weight=2)
    run.main.result("m1a", is_error=True)
    run.main.turn(bash("m1b", mark(1)), weight=4)
    run.main.result("m1b")
    for n in (2, 3, 4):
        run.main.turn(agent(f"w{n}", brief(n), "sonnet"), weight=100)
        run.main.result(f"w{n}")
        run.main.turn(bash(f"m{n}", mark(n)), weight=100)
        run.main.result(f"m{n}")
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out)[("phase", 1)] == 7


def test_phase_1_breaking_leaves_the_whole_session_unattributed(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(weight=1)
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=2)
    run.main.result("w1")
    run.main.turn(weight=4)
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("unattributed", None): 7}


def test_a_heading_with_emphasis_marks_still_starts_its_phase(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    call = next(
        block
        for e in run.main.entries
        if e["type"] == "assistant"
        for block in e["message"]["content"]
        if block.get("id") == "w1"
    )
    call["input"]["prompt"] = "**" + brief(1).replace("## ", "", 1) + "**"
    _, out = attribute(run, tmp_path)
    assert ("phase", 1) in main_turn_weights(out)


def test_an_opus_call_with_the_heading_does_not_start_a_phase(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("r", brief(1), "opus"), weight=1)
    run.main.result("r")
    run.main.turn(bash("m1", mark(1)), weight=2)
    run.main.result("m1")
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("unattributed", None): 3}


# --price-only


def test_price_only_prices_the_transcripts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Run(arm="without")
    run.main.turn(weight=2)
    out = run.write(tmp_path)
    (out / "stream.jsonl").write_text("")  # a killed run: no result event
    assert usage.main(["--price-only", str(out)], fixtures=tmp_path / "fixtures") == 0
    expected = run.reported()[OPUS]["costUSD"]
    assert capsys.readouterr().out == f"spent {expected:.7f}\n"
    assert not (out / "usage.txt").exists()


def test_price_only_without_transcripts_is_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "run"
    out.mkdir()
    assert usage.main(["--price-only", str(out)], fixtures=tmp_path) == 0
    assert capsys.readouterr().out == "spent 0\n"


# Found by the review of US2 (2026-10-14): each case below was red first.


def test_a_synthetic_zero_token_message_is_no_turn(tmp_path: Path) -> None:
    # Claude Code writes API-error messages as model "<synthetic>" with zero usage.
    run = Run(arm="without")
    run.main.turn(weight=2)
    zero = {k: 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens")}
    run.main.entries.append(
        {
            "type": "assistant",
            "message": {
                "id": "msg_err",
                "model": "<synthetic>",
                "usage": {**zero, "cache_creation_input_tokens": 0},
                "content": [],
            },
        }
    )
    code, out = attribute(run, tmp_path)
    assert code == 0
    assert {p["model"] for p in parts(out)} == {OPUS}


def test_a_reported_model_with_no_tokens_and_no_cost_needs_no_price(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    reported = run.reported()
    reported["claude-mystery-9"] = {"inputTokens": 0, "outputTokens": 0, "costUSD": 0.0}
    code, _ = attribute(run, tmp_path, reported=reported)
    assert code == 0


def test_a_rate_limit_event_without_the_window_is_skipped(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    out = run.write(tmp_path)
    events = [json.loads(line) for line in (out / "stream.jsonl").read_text().splitlines()]
    for e in events:
        if e["type"] == "rate_limit_event":
            del e["rate_limit_info"]["unifiedWindows"]
    (out / "stream.jsonl").write_text(lines(events))
    assert usage.main([str(out)], fixtures=tmp_path / "fixtures") == 0
    assert "five_hour - -" in (out / "usage.txt").read_text()


def test_the_last_entry_of_a_message_carries_its_usage(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn(bash("a", "ls"), bash("b", "pwd"), weight=3)
    first = run.main.entries[0]["message"]
    first["usage"] = {**first["usage"], "output_tokens": 1}  # streamed early, then final
    code, out = attribute(run, tmp_path)
    assert code == 0
    assert parts(out)[0]["output"] == 30


def test_price_only_skips_a_truncated_last_line_and_counts_subagents(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = Run(arm="without")
    run.main.turn(weight=2)
    run.sub("x", SONNET)
    out = run.write(tmp_path)
    with (out / f"transcripts/{SESSION}.jsonl").open("a") as f:
        f.write('{"type": "assistant", "message": {"id": "cut"')
    assert usage.main(["--price-only", str(out)], fixtures=tmp_path / "fixtures") == 0
    expected = run.reported()[OPUS]["costUSD"] + run.reported()[SONNET]["costUSD"]
    assert capsys.readouterr().out == f"spent {expected:.7f}\n"


def test_start_and_marking_in_one_turn_hold(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), bash("m1", mark(1)), weight=1)
    run.main.result("w1")
    run.main.result("m1")
    for n in (2, 3, 4):
        run.main.turn(agent(f"w{n}", brief(n), "sonnet"), weight=2)
        run.main.result(f"w{n}")
        run.main.turn(bash(f"m{n}", mark(n)), weight=2)
        run.main.result(f"m{n}")
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out)[("phase", 1)] == 1
    assert ("unattributed", None) not in main_turn_weights(out)


def test_marking_and_the_next_start_in_one_turn_break(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1", mark(1)), agent("w2", brief(2), "sonnet"), weight=2)
    run.main.result("m1")
    run.main.result("w2")
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("unattributed", None): 3}


def test_a_marking_without_a_tool_result_is_no_marking(tmp_path: Path) -> None:
    run = Run()
    run.main.turn(agent("w1", brief(1), "sonnet"), weight=1)
    run.main.result("w1")
    run.main.turn(bash("m1", mark(1)), weight=2)  # its result never came
    _, out = attribute(run, tmp_path)
    assert main_turn_weights(out) == {("unattributed", None): 3}


def test_a_marking_through_git_dash_c_counts(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    call = next(
        block
        for e in run.main.entries
        if e["type"] == "assistant"
        for block in e["message"]["content"]
        if block.get("id") == "m1"
    )
    call["input"]["command"] = 'git -C . commit -qm "fixture: tasks: mark phase 1"'
    _, out = attribute(run, tmp_path)
    assert ("unattributed", None) not in main_turn_weights(out)


def test_a_subagent_matching_no_call_has_no_phase(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    run.sub("ghost-w", SONNET)
    run.sub("ghost-r", OPUS, model="opus")
    _, out = attribute(run, tmp_path)
    nulls = {(p["part"], p["phase"]) for p in parts(out) if p["phase"] is None}
    assert ("worker", None) in nulls and ("review", None) in nulls


def test_parts_count_their_subagents(tmp_path: Path) -> None:
    run = Run(arm="without")
    run.main.turn()
    for n in (1, 2):
        run.main.turn(agent(f"r{n}", "Review", "opus"))
        run.main.result(f"r{n}")
        run.sub(f"r{n}", OPUS, model="opus")
    _, out = attribute(run, tmp_path)
    review = next(p for p in parts(out) if p["part"] == "review")
    assert review["subagents"] == 2
    assert next(p for p in parts(out) if p["part"] == "main")["subagents"] == 0


def test_usage_txt_lists_parts_in_session_order(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    _, out = attribute(run, tmp_path)
    order = [
        line.split()[1] + (line.split()[3] if line.split()[1] == "phase" else "")
        for line in (out / "usage.txt").read_text().splitlines()
        if line.startswith("part ") and OPUS in line
    ]
    assert order == ["before", "phase1", "phase2", "phase3", "phase4", "after"]


def test_phases_are_read_at_the_measured_commit(tmp_path: Path) -> None:
    run = Run()
    well_formed(run)
    out = run.write(tmp_path)
    # The fixture's headings change after the run's commit (a later hardening).
    tasks = tmp_path / "fixtures/fx/project/specs/001-fx/tasks.md"
    tasks.write_text(tasks.read_text().replace("Phase 2: User Story 1", "Phase 2: Story One"))
    assert usage.main([str(out)], fixtures=tmp_path / "fixtures") == 0
    assert ("unattributed", None) not in main_turn_weights(out)
