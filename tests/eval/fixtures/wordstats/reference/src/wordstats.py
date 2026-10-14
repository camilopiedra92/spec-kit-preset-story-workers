"""Word statistics: the reference implementation the held-out tests are proven against."""

import re
from collections import Counter

# A run of letters and digits, joined by single apostrophes between them.
WORD = re.compile(r"[^\W_]+(?:'[^\W_]+)*")


def words(text: str) -> list[str]:
    return WORD.findall(text)


def count_words(text: str) -> int:
    return len(words(text))


def top_words(text: str, n: int) -> list[tuple[str, int]]:
    if n < 0:
        raise ValueError("n must not be negative")
    counts = Counter(word.lower() for word in words(text))
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:n]
