# Tasks: Word statistics

**Input**: `specs/001-wordstats/` (spec.md, plan.md)

**Tests**: requested; each story's tests are written first and seen failing.

## Phase 1: Setup

- [ ] T001 Create `src/wordstats.py` with a module docstring, and `tests/` with a `conftest.py` that is empty but for a docstring; `uv run pytest` and `uv run ruff check` run

## Phase 2: User Story 1 - Count the words in a text (Priority: P1)

- [ ] T002 [US1] Write `tests/test_count_words.py`: one test per acceptance scenario of User Story 1; run it and see it fail
- [ ] T003 [US1] Implement the tokenizer of FR-001 and `count_words` in `src/wordstats.py`; `uv run pytest` and `uv run ruff check` pass

## Phase 3: User Story 2 - The most frequent words (Priority: P2)

- [ ] T004 [US2] Write `tests/test_top_words.py`: one test per acceptance scenario of User Story 2; run it and see it fail
- [ ] T005 [US2] Implement `top_words` in `src/wordstats.py` on the same tokenizer; `uv run pytest` and `uv run ruff check` pass

## Dependencies

Phase 1 → Phase 2 → Phase 3.
