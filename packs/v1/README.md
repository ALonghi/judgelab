# Python backend practice

This repo is intentionally incomplete. The tests define the required behavior.
Your job is to implement/refactor the code until the tests pass.

The exercises cover Python backend code, FastAPI, concurrency/asyncio, reliable
data handling, multi-tenant boundaries, and LLM-style streaming.

## Setup

Using `uv`:

```bash
cd packs/v1
uv sync
uv run pytest -q
```

Or using a virtualenv:

```bash
cd packs/v1
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest -q
```

## Rules for practice

1. Do the exercises without ChatGPT/Copilot/autocomplete first.
2. Talk out loud while coding:
   - state assumptions,
   - choose the simplest correct design,
   - mention complexity / failure modes,
   - only refactor after you have a working path.
3. Do **not** change the tests unless a test itself is clearly broken.
4. Prefer readable Python over clever Python.
5. After passing each exercise, answer the follow-up questions in its source file.

## Suggested interview simulation

### Exercise 1 — bounded async document fetching
Timebox: **30 minutes**

Focus:
- `asyncio`
- bounded concurrency
- deduplication
- ordering
- timeout/error isolation

Run:

```bash
pytest -q tests/test_exercise1_fetch_documents.py
```

### Exercise 2 — tenant-scoped FastAPI search
Timebox: **30–40 minutes**

Focus:
- FastAPI request validation
- Pydantic response models
- tenant boundaries
- repository/service separation
- HTTP semantics

Run:

```bash
pytest -q tests/test_exercise2_search_api.py
```

Optional local server after implementation:

```bash
uvicorn practice.exercise2_search_api:app --reload
```

### Exercise 3 — idempotent ingestion
Timebox: **25–30 minutes**

Focus:
- idempotency
- update semantics
- composite identity
- reasoning about DB constraints/transactions

Run:

```bash
pytest -q tests/test_exercise3_ingestion.py
```

### Exercise 4 — LLM-style async streaming
Timebox: **35 minutes**

Focus:
- async iterators
- timeouts
- fallback semantics
- partial output
- cancellation/error propagation

Run:

```bash
pytest -q tests/test_exercise4_llm_stream.py
```

### Exercise 5 — debug/refactor bad async Python
Timebox: **25 minutes**

Focus:
- blocking the event loop
- mutable defaults
- exception handling
- concurrency behavior
- explaining *why* code is problematic

Run:

```bash
pytest -q tests/test_exercise5_refactor.py
```

## Recommended order if you only have 2 hours

1. Exercise 1
2. Exercise 2
3. Exercise 4
4. Exercise 5 if time remains

## What to say during the interview

Good narration:

> "I'll start with the simplest correct implementation. Since the input can be
> large, I don't want unbounded concurrency, so I'll put the downstream call
> behind a semaphore."

Less useful narration:

> "Now I'm making a dictionary. Now I'm making a loop."

When you finish a working version, proactively mention one or two production
considerations, but don't redesign the whole system unless asked.
