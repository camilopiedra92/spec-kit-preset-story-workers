# checkout

Shopping-cart pricing with tax, promotions and returns, in `src/checkout/`.

## Commands

```bash
uv run pytest         # the suite
uv run ruff check     # the static check
```

## Conventions

- Every commit message starts with `fixture:`.
- Each user story closes with a fresh review: once a story's tasks are done, start a
  `general-purpose` subagent that reads the story's changes against
  `specs/001-checkout/spec.md` and reports what does not meet it; fix what it proves before the
  next story.
