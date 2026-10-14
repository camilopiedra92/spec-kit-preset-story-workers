# Feature Specification: Word statistics

**Feature Branch**: `001-wordstats`

**Status**: Ready

## User Scenarios & Testing

### User Story 1 - Count the words in a text (Priority: P1)

A writer passes a text and gets how many words it has.

**Independent Test**: `count_words` on the texts below returns the counts below.

**Acceptance Scenarios**:

1. **Given** an empty text or one of whitespace only, **When** its words are counted, **Then** the
   count is 0.
2. **Given** `"Hello, world!"`, **When** its words are counted, **Then** the count is 2:
   punctuation is not a word and does not join words.
3. **Given** `"don't stop"`, **When** its words are counted, **Then** the count is 2: an apostrophe
   between letters stays inside the word.
4. **Given** `"one\ntwo\tthree  four"`, **When** its words are counted, **Then** the count is 4: any
   run of whitespace separates words.
5. **Given** `"R2-D2 has 3 legs"`, **When** its words are counted, **Then** the count is 5: digits
   are word characters, and a hyphen separates words.

### User Story 2 - The most frequent words (Priority: P2)

A writer passes a text and a number n and gets the n most frequent words with their counts.

**Independent Test**: `top_words` on the texts below returns the lists below.

**Acceptance Scenarios**:

1. **Given** `"the cat and the hat and the bat"` and n = 2, **When** the top words are asked for,
   **Then** the result is `[("the", 3), ("and", 2)]`.
2. **Given** `"The THE the"` and n = 1, **When** the top words are asked for, **Then** the result is
   `[("the", 3)]`: words are compared case-insensitively and reported in lower case.
3. **Given** `"b a c b a c"` and n = 3, **When** the top words are asked for, **Then** the result is
   `[("a", 2), ("b", 2), ("c", 2)]`: equal counts are ordered alphabetically.
4. **Given** `"one two"` and n = 10, **When** the top words are asked for, **Then** the result is
   `[("one", 1), ("two", 1)]`: n larger than the distinct words returns them all.
5. **Given** any text and n = 0, **When** the top words are asked for, **Then** the result is `[]`;
   **Given** n < 0, **Then** `ValueError` is raised.

## Requirements

- **FR-001**: A word is a maximal run of letters, digits and apostrophes, where an apostrophe counts
  only between two letters or digits; everything else separates words.
- **FR-002**: `count_words` returns the number of words in a text (User Story 1).
- **FR-003**: `top_words` returns at most n `(word, count)` pairs, words in lower case, ordered by
  count descending, then word ascending (User Story 2), with the same definition of a word.
