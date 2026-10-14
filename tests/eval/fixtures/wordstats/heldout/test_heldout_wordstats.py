"""Held-out acceptance tests: one per acceptance scenario of the fixture's spec.

Never in the fixture: run.sh copies them into the scratch repository only after
the agent has finished, so no arm sees them, and every arm is judged by them.
"""

import importlib
from types import ModuleType

import pytest


@pytest.fixture
def ws() -> ModuleType:
    # Imported per test, not at the top: a missing module or function then fails
    # each test it affects, and the total stays the number of scenarios tested.
    return importlib.import_module("wordstats")


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_us1_s1_empty_or_whitespace_counts_zero(ws: ModuleType, text: str) -> None:
    assert ws.count_words(text) == 0


def test_us1_s2_punctuation_is_not_a_word(ws: ModuleType) -> None:
    assert ws.count_words("Hello, world!") == 2


def test_us1_s3_an_inner_apostrophe_stays_in_the_word(ws: ModuleType) -> None:
    assert ws.count_words("don't stop") == 2


def test_us1_s4_any_whitespace_run_separates(ws: ModuleType) -> None:
    assert ws.count_words("one\ntwo\tthree  four") == 4


def test_us1_s5_digits_are_word_characters_and_a_hyphen_separates(ws: ModuleType) -> None:
    assert ws.count_words("R2-D2 has 3 legs") == 5


def test_us2_s1_the_most_frequent_first(ws: ModuleType) -> None:
    assert ws.top_words("the cat and the hat and the bat", 2) == [("the", 3), ("and", 2)]


def test_us2_s2_case_insensitive_reported_lower(ws: ModuleType) -> None:
    assert ws.top_words("The THE the", 1) == [("the", 3)]


def test_us2_s3_ties_alphabetical(ws: ModuleType) -> None:
    assert ws.top_words("b a c b a c", 3) == [("a", 2), ("b", 2), ("c", 2)]


def test_us2_s4_n_beyond_distinct_returns_all(ws: ModuleType) -> None:
    assert ws.top_words("one two", 10) == [("one", 1), ("two", 1)]


def test_us2_s5_n_zero_is_empty(ws: ModuleType) -> None:
    assert ws.top_words("a b c", 0) == []


def test_us2_s5_n_negative_raises(ws: ModuleType) -> None:
    with pytest.raises(ValueError):
        ws.top_words("a b c", -1)
