"""compare.py: the verdict across runs, the gate, and the eval's spend.

Each test writes committed-shape run directories (data model, "Run directory")
for a one-story fixture with N = 4 held-out tests, so every criterion can be
pushed across its boundary by editing one file.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import compare
import pytest

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
N = 4
TASKS = "## Phase 1: Setup\n\n- [ ] T001 a\n- [ ] T002 b\n\n## Phase 2: US1\n\n- [ ] T003 c\n"
SPEC = "# Spec\n\n### User Story 1 - One (Priority: P1)\n\n### User Story 2 - Two (Priority: P2)\n"
VERSIONS = {
    "commit": "abc",
    "claude": "2.1.299",
    "specify": "1.1.3",
    "fixture": "fx",
    "autoupdater": "disabled",
    "skills": "speckit-implement",
}


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    fixtures = tmp_path / "fixtures"
    project = fixtures / "fx/project"
    (project / "specs/001-fx").mkdir(parents=True)
    (project / ".specify").mkdir()
    (project / ".specify/feature.json").write_text('{"feature_directory": "specs/001-fx"}\n')
    (project / "specs/001-fx/tasks.md").write_text(TASKS)
    (project / "specs/001-fx/spec.md").write_text(SPEC)
    (fixtures / "fx/heldout").mkdir()
    (fixtures / "fx/heldout/N").write_text(f"{N}\n")
    # wordstats: 001's fixture, 2 task lines, for the unmeasured estimate's ratio.
    ws = fixtures / "wordstats/project"
    (ws / "specs/001-ws").mkdir(parents=True)
    (ws / ".specify").mkdir()
    (ws / ".specify/feature.json").write_text('{"feature_directory": "specs/001-ws"}\n')
    (ws / "specs/001-ws/tasks.md").write_text("- [ ] T001 a\n- [ ] T002 b\n")
    baseline = tmp_path / "results/2026-10-14/without"
    baseline.mkdir(parents=True)
    (baseline / "usage.txt").write_text(
        "claude-opus-5-5 0.6 cache_read 1 cache_creation 1\nsum 0.6\n"
    )
    # The fixtures in a repository of their own: a run is judged by the fixture as
    # committed at the commit its versions.txt names.
    monkeypatch.setitem(VERSIONS, "commit", commit_all(tmp_path, "fixture"))
    probes = tmp_path / "probes.txt"
    probes.write_text(
        "claude 2.1.299 (Claude Code)\nok   R1 1: x\nok   R1 3: y\nprobes: 2 ok, 0 FAIL\n"
    )
    return {
        "root": tmp_path / "attempt",
        "fixtures": fixtures,
        "results": tmp_path / "results",
        "probes": probes,
    }


def commit_all(root: Path, message: str) -> str:
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root)]
    if not (root / ".git").exists():
        subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A", "fixtures"], check=True)
    subprocess.run([*git, "commit", "-qm", message], check=True)
    return subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def usage_json(costs: dict[str, float]) -> dict[str, Any]:
    models = {}
    parts = []
    for model, c in costs.items():
        t = {"input": 1, "output": 2, "cache_read": 3, "cache_write_5m": 4, "cache_write_1h": 5}
        # As usage.py writes it: `reported` is modelUsage's, one cache-write total.
        reported = {"input": 1, "output": 2, "cache_read": 3, "cache_write": 9, "cost": c}
        models[model] = {"reported": reported, "transcripts": {**t, "cost": c}}
        parts.append({"part": "main", "phase": None, "model": model, **t, "cost": c})
    return {"models": models, "parts": parts}


def write_run(
    root: Path,
    name: str,
    arm: str,
    cost: float,
    passed: int = N,
    suite: int = 0,
    **over: Any,
) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "status").write_text(over.get("status", "ok") + "\n")
    versions = {**VERSIONS, "arm": arm, "date": f"2026-10-15T0{len(name) % 10}:00:00Z"}
    versions.update(over.get("versions", {}))
    (d / "versions.txt").write_text("".join(f"{k}: {v}\n" for k, v in versions.items()))
    collected = over.get("collected", N)
    (d / "heldout.txt").write_text(f"passed {passed}/{collected}\n...\n")
    (d / "suite.txt").write_text(f"5 passed\nexit: {suite}\n")
    costs = {OPUS: cost} if arm != "with" else {OPUS: cost * 0.7, SONNET: cost * 0.3}
    (d / "usage.json").write_text(json.dumps(over.get("usage", usage_json(costs))))
    result = {"type": "result", "modelUsage": {m: {"costUSD": c} for m, c in costs.items()}}
    (d / "stream.jsonl").write_text(json.dumps(result) + "\n")
    agents = {
        "without": "agent general-purpose - - 2\n",
        "with": "agent general-purpose sonnet medium 4\nagent general-purpose opus - 2\n",
        "fallback": "",
    }[arm]
    (d / "models.txt").write_text(
        f"model {OPUS}\nmain {OPUS} effort medium\n" + over.get("agents", agents)
    )
    report = over.get(
        "report",
        "Carried out in this session: none"
        if arm != "fallback"
        else "Carried out in this session: T001, T002, T003",
    )
    (d / "report.txt").write_text(report + "\n")
    if arm == "with":
        (d / "attribution.txt").write_text(over.get("attribution", "ok   a\nok   b\n\nls\n"))
    return d


def nine(root: Path, without: float = 10.0, with_: float = 6.0, **over: Any) -> list[Path]:
    runs = []
    for n in (1, 2, 3):
        runs.append(write_run(root, f"without-{n}", "without", without + n, passed=N - (n == 1)))
        runs.append(write_run(root, f"with-{n}", "with", with_ + n, **over))
        runs.append(write_run(root, f"fallback-{n}", "fallback", 9.0 + n))
    return runs


def verdict(
    env: dict[str, Path], runs: list[Path], capsys: pytest.CaptureFixture[str]
) -> tuple[int, str]:
    code = compare.main(
        ["--probes", str(env["probes"]), *map(str, runs)],
        fixtures=env["fixtures"],
        results=env["results"],
    )
    return code, capsys.readouterr().out


def line(out: str, key: str) -> str:
    return next(l for l in out.splitlines() if l.startswith(key))


# The verdict.


def test_every_criterion_holding_exits_0(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = verdict(env, nine(env["root"]), capsys)
    assert code == 0, out
    for key in ("gate", "SC-001", "SC-002", "SC-003", "SC-005", "SC-006", "SC-007", "SC-008"):
        assert line(out, key).split()[1].rstrip(":") in ("ok", "open"), line(out, key)


def test_medians_and_spread_are_printed(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, out = verdict(env, nine(env["root"]), capsys)
    assert "without median $12.0000 min $11.0000 max $13.0000" in out
    assert "with median $8.0000 min $7.0000 max $9.0000" in out


def test_sc001_at_exactly_30_percent_passes(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # without medians 12; with medians 8.4 = 30% below.
    code, out = verdict(env, nine(env["root"], with_=6.4), capsys)
    assert line(out, "SC-001").startswith("SC-001 ok"), out
    assert code == 0


def test_sc001_just_under_30_percent_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = verdict(env, nine(env["root"], with_=6.41), capsys)
    assert line(out, "SC-001").startswith("SC-001 FAIL")
    assert code == 1


def test_sc002_tie_on_the_median_passes(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    # with's scores 4, 4, 3: median 4, as without's 3, 4, 4.
    (root / "with-3/heldout.txt").write_text("passed 3/4\n")
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-002").startswith("SC-002 ok"), out


def test_sc002_a_red_with_suite_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "with-2/suite.txt").write_text("1 failed\nexit: 1\n")
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-002").startswith("SC-002 FAIL")
    assert code == 1


def test_the_score_is_out_of_the_fixtures_n(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # A module that failed to collect shrinks the junit total to 2; the score is 2/4.
    root = env["root"]
    runs = nine(root)
    (root / "with-1/heldout.txt").write_text("passed 2/2\n")
    (root / "with-2/heldout.txt").write_text("passed 2/2\n")
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-002").startswith("SC-002 FAIL"), out
    assert "2/4" in out
    assert code == 1


def test_sc003_one_failing_clause_in_one_run_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "with-2/attribution.txt").write_text("ok   a\nFAIL b: wrote src/x.py\n")
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-003").startswith("SC-003 FAIL") and "with-2" in line(out, "SC-003")
    assert code == 1


def test_sc005_report_must_list_every_task_of_the_fixture(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "fallback-1/report.txt").write_text("Carried out in this session: T001, T003\n")
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-005").startswith("SC-005 FAIL") and "T002" in line(out, "SC-005")
    assert code == 1


def test_sc005_an_agent_call_in_fallback_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    with (root / "fallback-3/models.txt").open("a") as f:
        f.write("agent Explore - - 1\n")
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-005").startswith("SC-005 FAIL")


def test_sc006_versions_are_compared_as_major_minor_patch(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, out = verdict(env, nine(env["root"]), capsys)
    assert line(out, "SC-006").startswith("SC-006 ok")


def test_sc006_a_different_version_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    env["probes"].write_text("claude 2.1.300 (Claude Code)\nok   R1 1: x\nprobes: 1 ok, 0 FAIL\n")
    code, out = verdict(env, nine(env["root"]), capsys)
    assert line(out, "SC-006").startswith("SC-006 FAIL")
    assert code == 1


def test_sc006_a_failed_probe_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    env["probes"].write_text(
        "claude 2.1.299 (Claude Code)\nok   R1 1: x\nFAIL R1 5: thinking\nprobes: 1 ok, 1 FAIL\n"
    )
    _, out = verdict(env, nine(env["root"]), capsys)
    assert line(out, "SC-006").startswith("SC-006 FAIL")


def test_sc007_needs_a_review_per_story_of_the_fixture(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "with-1/models.txt").write_text(
        "agent general-purpose sonnet medium 4\nagent general-purpose opus - 1\nagent Explore - - 3\n"
    )
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-007").startswith("SC-007 FAIL") and "with-1" in line(out, "SC-007")
    assert code == 1


def test_sc008_parts_that_do_not_sum_fail(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    data = json.loads((root / "with-1/usage.json").read_text())
    data["parts"][0]["input"] += 1
    (root / "with-1/usage.json").write_text(json.dumps(data))
    code, out = verdict(env, runs, capsys)
    assert line(out, "SC-008").startswith("SC-008 FAIL")
    assert code == 1


def test_sc008_transcripts_that_differ_from_reported_fail(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    data = json.loads((root / "fallback-2/usage.json").read_text())
    data["models"][OPUS]["transcripts"]["cost"] += 1e-5
    (root / "fallback-2/usage.json").write_text(json.dumps(data))
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-008").startswith("SC-008 FAIL")


def test_a_closed_gate_fails_the_verdict(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "without-1/heldout.txt").write_text("passed 4/4\n")
    code, out = verdict(env, runs, capsys)
    assert line(out, "gate").startswith("gate closed")
    assert code == 1


# Refused input.


@pytest.mark.parametrize(
    "breaking",
    ["status", "two runs", "four runs", "fixture", "versions"],
)
def test_refused_input_exits_2(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str], breaking: str
) -> None:
    root = env["root"]
    runs = nine(root)
    if breaking == "status":
        (root / "with-1/status").write_text("not counted: exit 1\n")
    elif breaking == "two runs":
        runs = [r for r in runs if r.name != "with-3"]
    elif breaking == "four runs":
        runs.append(write_run(root, "with-4", "with", 7.0))
    elif breaking == "fixture":
        v = root / "with-1/versions.txt"
        v.write_text(v.read_text().replace("fixture: fx", "fixture: other"))
    else:
        v = root / "fallback-2/versions.txt"
        v.write_text(v.read_text().replace("claude: 2.1.299", "claude: 2.1.300"))
    code, _ = verdict(env, runs, capsys)
    assert code == 2


# The gate.


def test_gate_open_when_a_without_run_misses(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runs = [
        write_run(env["root"], f"without-{n}", "without", 10.0, passed=N - (n == 2))
        for n in (1, 2, 3)
    ]
    code = compare.main(
        ["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "gate open" in out and "3/4" in out


def test_gate_closed_when_every_without_run_is_perfect(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runs = [write_run(env["root"], f"without-{n}", "without", 10.0) for n in (1, 2, 3)]
    code = compare.main(
        ["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"]
    )
    assert code == 1
    assert "gate closed" in capsys.readouterr().out


def test_gate_refuses_other_than_three_without_runs(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runs = [write_run(env["root"], f"without-{n}", "without", 10.0) for n in (1, 2)]
    assert (
        compare.main(["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"])
        == 2
    )


# The spend.


def spent(env: dict[str, Path], capsys: pytest.CaptureFixture[str], *next_: str) -> str:
    args = ["--spent", str(env["root"].parent / "attempts")]
    if next_:
        args += ["--fixture", "fx", "--next", *next_]
    assert compare.main(args, fixtures=env["fixtures"], results=env["results"]) == 0
    return capsys.readouterr().out


def test_an_empty_root_has_spent_nothing(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    (env["root"].parent / "attempts").mkdir()
    out = spent(env, capsys)
    assert "spent 0" in out.splitlines()[-1]


def test_spend_counts_runs_probes_killed_and_refused_tries(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    attempts = env["root"].parent / "attempts/attempt-1"
    write_run(attempts, "without-1-1", "without", 2.0)
    # A killed try: no result event, its transcripts priced at the table.
    killed = attempts / "without-2-1"
    (killed / "transcripts").mkdir(parents=True)
    (killed / "status").write_text("not counted: deadline: 3600 s\n")
    (killed / "stream.jsonl").write_text('{"type": "system", "subtype": "init"}\n')
    entry = {
        "type": "assistant",
        "message": {
            "id": "m1",
            "model": OPUS,
            "usage": {
                "input_tokens": 1_000_000,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0},
            },
        },
    }
    (killed / "transcripts/s.jsonl").write_text(json.dumps(entry) + "\n")
    # A refused try: nothing spent.
    refused = attempts / "without-2-2"
    refused.mkdir()
    (refused / "status").write_text("refused: versions differ from the baseline: claude\n")
    # A probe stream.
    (attempts / "probes").mkdir()
    probe = {"type": "result", "modelUsage": {OPUS: {"costUSD": 0.1}, SONNET: {"costUSD": 0.05}}}
    (attempts / "probes/r1-1.jsonl").write_text(json.dumps(probe) + "\n")
    out = spent(env, capsys)
    assert "attempt-1/without-2-1 4.0000000" in out  # 1M input tokens at $4
    assert "attempt-1/without-2-2 0 (no cost recorded)" in out
    assert out.splitlines()[-1] == "spent 6.1500000"


def test_next_estimates(env: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    attempts = env["root"].parent / "attempts/attempt-1"
    for n, c in ((1, 2.0), (2, 3.0), (3, 2.5)):
        write_run(attempts, f"without-{n}-1", "without", c)
    out = spent(env, capsys, "without", "with", "fallback")
    # without: 3 × its highest (3.0); with, fallback: 3 × 2 × the highest of any arm.
    assert "estimate without 9.0000000" in out
    assert "estimate with 18.0000000 (provisional)" in out
    assert "estimate fallback 18.0000000 (provisional)" in out
    assert "estimate total 45.0000000 worst case 135.0000000" in out


def test_next_before_any_counted_run_is_scaled_from_001(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    (env["root"].parent / "attempts").mkdir()
    out = spent(env, capsys, "without")
    # 001's without $0.6 × (3 task lines / 2) per run, three runs.
    assert "estimate without 2.7000000 (unmeasured)" in out


def test_help_prints_the_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert compare.main(["--help"]) == 0
    assert "--spent <root>" in capsys.readouterr().out


def test_sc008_a_cache_write_total_that_differs_from_the_split_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    data = json.loads((root / "with-3/usage.json").read_text())
    data["models"][OPUS]["reported"]["cache_write"] += 1
    (root / "with-3/usage.json").write_text(json.dumps(data))
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-008").startswith("SC-008 FAIL")


# Found by the review of US3 (2026-10-14).


def test_spent_does_not_count_a_run_twice_through_its_link(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    attempts = env["root"].parent / "attempts"
    for k in (1, 2):
        a = attempts / f"attempt-{k}"
        write_run(a, "without-1-1", "without", 1.0)
        (a / "without-1").symlink_to("without-1-1")
    out = spent(env, capsys)
    assert "attempt-1/without-1-1 1.0000000" in out
    assert "attempt-2/without-1-1 1.0000000" in out
    assert out.splitlines()[-1] == "spent 2.0000000"


def test_spent_prices_an_interrupted_try_without_a_status(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    try_ = env["root"].parent / "attempts/attempt-1/without-1-1"
    (try_ / "transcripts").mkdir(parents=True)
    (try_ / "stream.jsonl").write_text('{"type": "system", "subtype": "init"}\n')
    entry = {
        "type": "assistant",
        "message": {
            "id": "m",
            "model": OPUS,
            "usage": {"input_tokens": 500_000, "output_tokens": 0, "cache_read_input_tokens": 0},
        },
    }
    (try_ / "transcripts/s.jsonl").write_text(json.dumps(entry) + "\n")
    out = spent(env, capsys)
    assert out.splitlines()[-1] == "spent 2.0000000"


def test_spent_on_a_missing_root_is_refused(env: dict[str, Path]) -> None:
    code = compare.main(
        ["--spent", str(env["root"] / "nowhere")], fixtures=env["fixtures"], results=env["results"]
    )
    assert code == 2


def test_sc003_ignores_fail_in_the_listed_bash_commands(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "with-1/attribution.txt").write_text(
        "ok   a\nok   b\n\nmain session's Bash commands:\n"
        '  uv run pytest -q 2>&1 | grep -E "FAILED|passed"\n'
    )
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-003").startswith("SC-003 ok"), out


@pytest.mark.parametrize(
    "report",
    [
        "Carried out in this session: T001–T003",
        "Carried out in this session: T001 to T003.",
        "__Carried out in this session:__ T001, T002, T003",
        "Carried out in this session: none\n\nCarried out in this session: T001-T003",
    ],
)
def test_sc005_reads_ranges_emphasis_and_the_last_report_line(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str], report: str
) -> None:
    root = env["root"]
    runs = nine(root)
    for n in (1, 2, 3):
        (root / f"fallback-{n}/report.txt").write_text(report + "\n")
    _, out = verdict(env, runs, capsys)
    assert line(out, "SC-005").startswith("SC-005 ok"), out


def test_sc006_a_truncated_probes_file_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    env["probes"].write_text("claude 2.1.299 (Claude Code)\nok   R1 1: x\n")
    _, out = verdict(env, nine(env["root"]), capsys)
    assert line(out, "SC-006").startswith("SC-006 FAIL")


def test_the_same_run_given_twice_is_refused(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root = env["root"]
    runs = nine(root)
    (root / "with-link").symlink_to("with-1")
    runs = [r for r in runs if r.name != "with-3"] + [root / "with-link"]
    code, _ = verdict(env, runs, capsys)
    assert code == 2


def test_runs_are_judged_by_the_fixture_at_their_own_commit(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # A hardening after the runs: N grows from 4 to 6 in a later commit.
    runs = [write_run(env["root"], f"without-{n}", "without", 10.0) for n in (1, 2, 3)]
    (env["fixtures"] / "fx/heldout/N").write_text("6\n")
    commit_all(env["fixtures"].parent, "harden")
    code = compare.main(
        ["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"]
    )
    out = capsys.readouterr().out
    assert code == 1, out
    assert "gate closed" in out and "4/4" in out


def test_a_commit_the_repository_lacks_is_refused(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runs = [
        write_run(env["root"], f"without-{n}", "without", 10.0, versions={"commit": "f" * 40})
        for n in (1, 2, 3)
    ]
    assert (
        compare.main(["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"])
        == 2
    )


def test_a_run_whose_held_out_total_is_not_n_is_refused(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # Extra tests collected (a conftest in the agent's work) would let failures pass
    # unseen; fewer collected is scored out of N already.
    root = env["root"]
    runs = nine(root)
    (root / "without-2/heldout.txt").write_text(f"passed {N}/{N + 2}\n")
    code, _ = verdict(env, runs, capsys)
    assert code == 2


def test_a_probe_summary_with_no_ok_fails(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    env["probes"].write_text("claude 2.1.299 (Claude Code)\nprobes: 0 ok, 0 FAIL\n")
    _, out = verdict(env, nine(env["root"]), capsys)
    assert line(out, "SC-006").startswith("SC-006 FAIL")


def test_gate_refuses_a_run_that_collected_beyond_n(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    runs = [write_run(env["root"], f"without-{n}", "without", 10.0) for n in (1, 2, 3)]
    (env["root"] / "without-3/heldout.txt").write_text(f"passed {N}/{N + 2}\n")
    code = compare.main(
        ["--gate", *map(str, runs)], fixtures=env["fixtures"], results=env["results"]
    )
    assert code == 2


def test_a_run_with_no_junit_report_scores_zero(
    env: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # run.sh's line when pytest left no report: the run is scored 0 of N, not refused.
    root = env["root"]
    runs = nine(root)
    (root / "with-1/heldout.txt").write_text("passed 0/0: no junit report\n")
    (root / "with-2/heldout.txt").write_text("passed 0/0: no junit report\n")
    code, out = verdict(env, runs, capsys)
    assert code == 1, out
    assert line(out, "SC-002").startswith("SC-002 FAIL") and f"0/{N}" in out
