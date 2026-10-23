"""Checks the composed speckit-implement skill's Story workers fragment against the rule
mapping of specs/004-fragment-form-and-observation (US1): every block of the fragment is a
row of plan.md's mapping, in order, and every inventoried rule of spec.md has exactly one row.

Usage:  tests/fragment_rules.py <composed SKILL.md> <plan.md> <spec.md> <README.md>
Exit:   0 holds; 1 a problem, each named; 2 unreadable input

What it proves: no rule of the inventory lacks a bullet, none is duplicated, none is extra, the
text is the mapped text, the order is the mapped order, the justification sentences are in the
README. What it cannot prove: that a bullet still MEANS what the old clause did; a fresh-context
reviewer compares the inventory with the old and the new text for that (spec, US1).
"""

import re
import sys
from collections import Counter
from pathlib import Path

HEADING = "## Story workers"


def squeeze(text: str) -> str:
    return " ".join(text.split())


def table(text: str, first: str) -> list[list[str]]:
    """The cells of each markdown table row whose first cell matches `first`."""
    rows = []
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if re.fullmatch(first, cells[0]):
                rows.append(cells)
    return rows


def blocks(skill: str) -> list[tuple[bool, str]]:
    """The fragment's blocks as (is_bullet, squeezed text), from its last heading to the end."""
    lines = skill.splitlines()
    start = max(i for i, line in enumerate(lines) if line == HEADING)
    found: list[tuple[bool, list[str]]] = []
    current: tuple[bool, list[str]] | None = None
    for line in lines[start:]:
        if not line.strip():
            current = None
        elif line.startswith("- "):
            current = (True, [line[2:]])
            found.append(current)
        elif current is not None and (not current[0] or line.startswith("  ")):
            current[1].append(line)
        else:
            current = (False, [line])
            found.append(current)
    return [(bullet, squeeze(" ".join(parts))) for bullet, parts in found]


def check(skill: str, plan: str, spec: str, readme: str) -> list[str]:
    problems: list[str] = []
    mapping = [(k, r, squeeze(t)) for k, r, t in table(plan, "[HPLB]")]
    if not mapping:
        return ["plan.md has no mapping rows"]
    # The mapping: a rule per paragraph and bullet, once; headings and labels carry none.
    seen: dict[str, int] = {}
    for kind, rule, _ in mapping:
        if kind in "PB":
            if not re.fullmatch(r"[RN]\d+", rule):
                problems.append(f"mapping row without a rule id: {rule!r}")
            seen[rule] = seen.get(rule, 0) + 1
        elif rule != "-":
            problems.append(f"a {kind} row carries a rule: {rule}")
    problems += [f"{r} is mapped to {n} blocks" for r, n in seen.items() if n > 1]
    inventory = {c[0] for c in table(spec, r"R\d+")}
    new = {c[0] for c in table(spec, r"N\d+")}
    mapped_r = {r for r in seen if r.startswith("R")}
    problems += [f"{r} is in the inventory and has no block" for r in sorted(inventory - mapped_r)]
    problems += [
        f"{r} has a block and is not in the inventory" for r in sorted(mapped_r - inventory)
    ]
    problems += [
        f"{r} has a block and is not in the new rules"
        for r in sorted({r for r in seen if r.startswith("N")} - new)
    ]
    numbers = sorted(int(r[1:]) for r in inventory)
    if numbers != list(range(1, len(numbers) + 1)):
        problems.append("the inventory's ids are not R1..Rn without a gap")
    ids_in_order = [int(r[1:]) for k, r, _ in mapping if k in "PB" and r.startswith("R")]
    if ids_in_order != sorted(ids_in_order):
        problems.append("the mapping's rules are not in the inventory's order")
    # The composed fragment against the mapping, block by block.
    try:
        actual = blocks(skill)
    except ValueError:
        return [*problems, f"the composed skill has no {HEADING!r}"]
    want = [(kind == "B", text) for kind, _, text in mapping]
    owner = {text: rule for _, rule, text in mapping}
    have, wanted = Counter(actual), Counter(want)
    for block in want:
        if have[block] == 0:
            problems.append(f"{owner[block[1]]}: block missing: {block[1][:70]!r}")
    for block in have:
        if block not in wanted:
            problems.append(f"a block the mapping lacks: {block[1][:70]!r}")
        elif have[block] > wanted[block]:
            problems.append(f"{owner[block[1]]}: block appears {have[block]} times")
    if not problems and actual != want:
        problems.append("the fragment's blocks are in a different order than the mapping")
    # The justification sentences live in the README under their ids.
    for jid in (c[0] for c in table(spec, r"J\d+")):
        if not re.search(rf"\*\*{jid}\*\*", readme):
            problems.append(f"{jid} (a justification sentence) is not in the README as **{jid}**")
    return problems


def main(argv: list[str]) -> int:
    try:
        skill, plan, spec, readme = (Path(a).read_text(encoding="utf-8") for a in argv)
    except (OSError, ValueError) as error:
        print(f"fragment_rules.py: {error}", file=sys.stderr)
        return 2
    problems = check(skill, plan, spec, readme)
    for problem in problems:
        print(f"FAIL {problem}")
    if not problems:
        count = len(table(plan, "[PB]"))
        print(f"ok: {count} blocks, each one rule of the inventory, in the mapped order")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
