# Implementation Plan: Word statistics

**Branch**: `001-wordstats` | **Spec**: [spec.md](spec.md)

## Summary

Two functions in one module, built on one tokenizer, so both stories agree on what a word is.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: none at runtime; pytest and ruff for development, through uv.

**Testing**: `uv run pytest` (the suite) and `uv run ruff check` (the static check).

**Project Type**: a library module.

## Interface

`src/wordstats.py`:

- `count_words(text: str) -> int`
- `top_words(text: str, n: int) -> list[tuple[str, int]]`

Tests live in `tests/`, one file per story: `tests/test_count_words.py`, `tests/test_top_words.py`.

## Project Structure

```text
src/wordstats.py
tests/test_count_words.py
tests/test_top_words.py
```
