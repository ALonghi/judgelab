# Progressive Python practice

**Python 3.13+ · general coding · progressive requirements · architecture discussions**

Explore data handling, decomposition, edge cases and extensions through a small
synthetic document corpus. Scores, permissions, budgets and event protocols are
simplified exercise contracts. See SOURCES.md for technical references.

## Start locally

Open `packs/v2` as your editor's project root. Python must already be installed.

### macOS / Linux

```bash
cd packs/v2
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python tools/check_setup.py
python -m pytest -q tests/test_setup.py
```

### Windows PowerShell

```powershell
cd packs/v2
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe tools\check_setup.py
.\.venv\Scripts\python.exe -m pytest -q tests	est_setup.py
```

Windows commands work without changing your PowerShell execution policy. In the
commands below, replace `python` with `.\.venv\Scripts\python.exe` when necessary.

Only pytest is installed as a runtime project dependency. All exercise code uses
the standard library; **no FastAPI, DB server, API keys, embeddings, model calls,
Docker, or network services** are required to run the exercises. Installing the
dependencies initially requires network access unless you have a local package cache.

Confirm your editor uses `.venv` as its interpreter, not an older global Python.
`tools/check_setup.py` prints the version and package path.

## Expected initial result

`tests/test_setup.py` should pass immediately. Exercise tests should fail because
of explicit TODOs. That is intentional, not a broken environment.

```bash
# First exercise only; stop after the first failure.
python -m pytest -q tests/test_01_warmup.py -x

# All tests, including intentionally unsolved exercises.
python -m pytest -q
```

The full suite contains 91 tests: 3 setup tests and 88 exercise cases (including
parametrized edge cases). Do not aim to solve all of them in one interview-length
session. See VALIDATION.md for what was checked before delivery.

## Your route through the code

| Round | Write in | Read first | Suggested time |
|---|---|---|---|
| 1. Warm-up: latest versions + category counts | `practice/round01_warmup.py` | `prompts/01_warmup.md` | 10–15 min |
| 2. Permission-aware ranked search | `practice/round02_search.py` | `prompts/02_search.md` | 25–35 min |
| 3. Retrieval context + source references | `practice/round03_context.py` | `prompts/03_context.md` | 25–35 min |
| 4. Out-of-order ingestion + tombstones | `practice/round04_ingestion.py` | `prompts/04_ingestion.md` | 25–35 min |
| 5. Async source fan-out + partial failures | `practice/round05_async.py` | `prompts/05_async.md` | 30–40 min |
| Bonus. Incremental chat-event parser | `practice/round06_stream_bonus.py` | `prompts/06_stream_bonus.md` | 20–30 min |

Each round has its own tests and supplied fixtures. You can attempt them
independently; a failing Round 1 does not block testing Round 2 or Round 3.
The times are optional practice suggestions.

Run a round:

```bash
python -m pytest -q tests/test_02_search.py -x
python -m pytest -q tests/test_03_context.py -x
python -m pytest -q tests/test_04_ingestion.py -x
python -m pytest -q tests/test_05_async.py -x
python -m pytest -q tests/test_06_stream_bonus.py -x
```

Focus on one topic within a round:

```bash
python -m pytest -q tests/test_02_search.py -k 'score or token or ties'
python -m pytest -q tests/test_02_search.py -k 'permissions or limits or category'
python -m pytest -q tests/test_04_ingestion.py -k 'delete or stale or restore'
```

Tests are the executable acceptance criteria. The source docstrings and prompt
files state all assessed requirements; there are no hidden production requirements.
Keep signatures/data models intact, but add private helpers where useful. Avoid
changing tests just to turn failures green. Add your own tests to a separate file.

## Two realistic practice sessions

### Session A: warm-up → search → changing requirements (about 70 min)

1. 10 min: Round 1A (`latest_documents`). State identity and tie rules first.
2. 25 min: Round 2. Start with ordinary ranking tests; add permissions and filters.
3. 20 min: Round 3, or finish Round 2 and demonstrate extra edge cases.
4. 10 min: answer search/context prompts in ARCHITECTURE_FOLLOWUPS.md.
5. 5 min: explain one bug you caught and one improvement you deliberately deferred.

### Session B: new warm-up → ingestion → reliability (about 70 min)

1. 5 min: Round 1B (`category_counts`).
2. 30 min: Round 4, adding stale events, deletions, and conflicts progressively.
3. 25 min: choose Round 5 **or** the stream-parser bonus; do not rush both.
4. 10 min: discuss the architecture consequences of what you just implemented.

### Only two hours available?

Do Round 1, Round 2, and one of Round 3 or 4. Spend the remaining time explaining
your choices and testing corner cases. Round 5 adds concurrency practice.

## How to practise

Read the prompt, write down a tiny example, and restate assumptions aloud. Deliver
a working simple version before optimizing. Then take one extension at a time and
rerun the relevant tests. Explain **why** a structure/contract is appropriate rather
than narrating each keystroke.

Try the first pass yourself, using syntax lookup or hints when needed. Practise the
same reasoning with renamed objects: invoices instead of documents, product feeds
instead of connectors, status updates instead of document versions.

## Provided scaffolding

- `practice/models.py`: immutable data records used by the exercises.
- `practice/text.py`: a toy tokenizer so regex syntax is not the main task.
- `practice/sample_data.py`: synthetic documents and chunks.
- `practice/demo.py`: small runnable examples for your completed implementations.
- `HINTS.md`: optional direction, not completed solutions.
- `ARCHITECTURE_FOLLOWUPS.md`: short prompts, not a full architecture course.

After solving a round:

```bash
python -m practice.demo warmup
python -m practice.demo search
python -m practice.demo context
python -m practice.demo ingestion
python -m practice.demo async
python -m practice.demo stream
```

Only the search **demo** combines Rounds 1 and 2. The tests remain independent.
An unsolved demo prints an explicit TODO message instead of pretending to work.

## A good result is more than “green tests”

Check that you can explain your definition of identity, ordering, permissions,
update/failure behavior, and memory/runtime cost. Distinguish the local exercise
contract from what would change with multiple workers, persistent storage, real
search scores, or changing authorization. Name an abstraction you would introduce
only when the requirements justify it.

Use `packs/v1` for extra FastAPI and async streaming practice.
