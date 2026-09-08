# Guided exercise: search documents without leaking other people's data

This is a guided version of **Round 2** in your earlier Python practice pack.
It preserves that exercise's data model, scoring, permissions, category semantics,
and public function signature. The three small helpers and stage tests are added
teaching scaffolding for the playground.

Plan for **60–90 minutes while learning**, not the earlier unguided timebox.
You may need longer; understanding comes before speed. Work through one stage,
run its tests, and only then move on. You do not need to implement an API, embeddings,
a classifier, a database, or async code.

## 0. Get it running

Run these commands from the repository root.

### macOS / Linux

```bash
cd packs/guided
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests/test_setup.py
```

### Windows PowerShell

```powershell
cd packs/guided
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q tests/test_setup.py
```

On Windows, use `.\.venv\Scripts\python.exe` in place of `python` in the remaining
commands. Use the virtual environment as your editor's interpreter.

You should initially see **3 passing setup tests**. Running the entire suite now
produces **44 failing exercise cases and 3 passes**. The failures are intentional:
the four functions in `exercise.py` raise `NotImplementedError`.

The only third-party dependency is pytest. Installation can require internet;
the exercises themselves do not use the network.

Edit **`exercise.py`**. Read `models.py`, `text_tools.py`, and `examples.py` when
needed, but leave them unchanged. `sandbox.py` is an optional scratchpad:

```bash
python sandbox.py
```

## 1. The problem in plain English

Alice works for customer `firm-a`. She searches for:

```text
termination notice
```

Write software that returns the highest-scoring matching documents she is allowed
to read, optionally restricted to selected categories. Equal scores must have a
predictable order. Asking for two results means the best two **eligible** matches,
not the first two records encountered.

In this exercise:

- A **tenant** is a customer firm. Customer firms have separate data boundaries.
- A **category** is an existing tag such as `contract` or `memo`. You are filtering
  assigned tags, not inventing a classification algorithm.
- A **token** is a lowercase ASCII word/number produced by the supplied helper.
  These are not an LLM's subword tokens.
- A **score** is the integer computed by the explicit rule below. It is not a
  confidence percentage or an AI model output.
- A **SearchHit** is a small output record: ID, title, and score.

You are building the selection/ranking piece. There is no answer generation or
complete RAG pipeline in this exercise.

## 2. Understand the provided records

Construct a document in `sandbox.py` like this:

```python
from models import Document

example = Document(
    tenant_id="firm-a",
    document_id="example",
    version=1,
    title="Termination clause",
    text="Notice of termination.",
    categories=frozenset({"contract"}),
    allowed_users=frozenset({"alice"}),
    public=False,
)

print(example.title)
print(example.text)
print("alice" in example.allowed_users)
```

`version` is supplied metadata but plays no role in this exercise. Inputs already
have unique `(tenant_id, document_id)` identities; do not add version selection.
The body field is named **`text`**, not `body` or `content`.

These are dataclass records: the constructor and field-based comparisons are
provided. `frozen=True` prevents ordinary field reassignment. `frozenset` is an
immutable set; membership and intersection work for our purposes. You do not need
to write your own record classes.

`public=True` means **public inside that tenant**, not available to other firms.
The caller's tenant and user identity are assumed already authenticated. Accepting
arbitrary identity claims from an HTTP client is outside this exercise.

## Stage 1 — score one document

Implement:

```python
def score_document(document: Document, query_terms: set[str]) -> int:
    ...
```

Ignore tenants, permissions, and categories for now. This helper answers only:
**how many points does this document earn for these words?**

### The supplied tokenizer

```python
from text_tools import terms

assert terms("Termination, NOTICE! notice") == {"termination", "notice"}
assert "notice" not in terms("notices")
assert terms("!?") == set()
```

You do not need to learn regex to complete this. The tokenizer is already written.
Its use of a set removes repetition. Sets have no meaningful display order, so
seeing `{'notice', 'termination'}` instead is fine.

### Scoring contract

For each **distinct query term**:

- Add 3 if that term appears in the title.
- Independently add 1 if it appears in the text.

A word in both contributes **4**. Repeating a word changes nothing. Matching one
query term is enough to get a positive score; a document need not match every term.

Work through the `example` above:

```text
Query: termination notice
Title: Termination clause
Text:  Notice of termination.

termination: title +3, text +1 => 4
notice:      title +0, text +1 => 1
TOTAL                           5
```

### Your implementation steps

Convert the title and text to token sets once each. Start a score at zero. Visit
query terms and add the appropriate contributions. Return the integer.

Use a normal loop first. A compact set-based version is optional after it works.
Do not use substring matching or occurrence counting. Do not remove items from
`query_terms`, because the same set will be reused for the next document.

**Watch for `if`/`elif`:** the title and text tests are independent. A match in the
title must not prevent checking the body.

Run:

```bash
python -m pytest -q tests/test_stages.py -k stage1 -x
```

Target: **9 passing cases**. They cover no matches, title only, body only, both,
multiple query terms, repetitions, whole-word matching, case/punctuation, and an
empty query.

When a test fails, read its small input and expected number. Calculate the number
by hand, then compare it to what your loop does.

## Stage 2 — decide whether Alice can read a document

Implement:

```python
def can_read(document: Document, *, tenant_id: str, user_id: str) -> bool:
    ...
```

The `*` makes the following arguments keyword-only. Call the helper as:

```python
can_read(example, tenant_id="firm-a", user_id="alice")
```

### Think of two gates

**Gate 1: customer boundary.** The document must belong to the caller's tenant.
Nothing else can override a failure here.

**Gate 2: document permission.** Within the correct tenant, it must be public OR
the current user must appear in `allowed_users`.

For Alice at firm-a:

```text
firm-a + public                         => readable
firm-a + private + allowed alice        => readable
firm-a + private + allowed bob only     => not readable
firm-b + public                         => not readable
firm-b + private + allowed alice        => not readable
```

That last example matters: a same-looking user identifier does not erase the
customer boundary.

Early returns are fine. A parenthesized Boolean expression is also fine. Keep the
business rule obvious rather than minimizing the number of characters.

Run:

```bash
python -m pytest -q tests/test_stages.py -k stage2 -x
```

Target: **7 passing cases**. Scoring should not appear in this function at all.

## Stage 3 — apply optional category filters

Implement:

```python
def matches_categories(
    document: Document,
    categories: frozenset[str] | None,
) -> bool:
    ...
```

The meaning of the input is deliberately precise:

```text
None                    => no category restriction
frozenset()             => match nothing
frozenset({'contract'}) => require 'contract'
frozenset({'memo', 'contract'}) => require either one
```

A document with no categories still passes when the requested filter is `None`.
Category names are exact and case-sensitive: `Memo` is not `memo`.

### Python tool to try

```python
assigned = frozenset({"contract", "employment"})
requested = frozenset({"memo", "contract"})

print(assigned & requested)       # frozenset({'contract'})
print(bool(assigned & requested)) # True
```

The `&` operation gives shared members. An empty intersection means there was no
shared category.

**Trap:** `if not categories` groups `None` and an empty set together. Their meaning
is different in this contract. Handle `None` explicitly before checking overlap.
Return a Boolean, not the intersection object.

Run:

```bash
python -m pytest -q tests/test_stages.py -k stage3 -x
```

Target: **7 passing cases**.

## Stage 4 — assemble the search function

Now implement `search_documents` using the three helpers.

The exact public signature is unchanged from your V2 pack. It must accept a list
or a one-pass iterable of documents and return a `list[SearchHit]`.

### Translate this plan into Python

```text
validate limit
prepare query terms once
if query has no terms, return an empty result

for each document:
    reject documents the user cannot read
    reject documents excluded by categories
    compute the score
    keep a SearchHit only when the score is positive

order hits by descending score and ascending document ID
return at most limit hits
```

The body of the function is yours to write; do not put everything in one long
comprehension. The explicit steps make it easier to inspect and change.

Create output records like:

```python
SearchHit(document_id="example", title="Example title", score=5)
```

### Validation must happen first

`limit` is an integer between 1 and 100 inclusive. Invalid values raise
`ValueError`, even when the input or query is empty or the category filter matches
nothing. This is the contract, not a rule you need to infer.

### Sorting in two directions

Here is an analogous operation on support tickets represented as `(priority, id)`:

```python
tickets = [(2, "z"), (5, "b"), (5, "a")]
ordered = sorted(tickets, key=lambda ticket: (-ticket[0], ticket[1]))
assert ordered == [(5, "a"), (5, "b"), (2, "z")]
```

The negative priority puts large priorities first; the ID remains ascending.
Adapt the idea to `SearchHit` fields. Applying `reverse=True` to both fields would
reverse the tie-break too, which is not the requested result.

Build/sort a separate results list. Do not reorder the input documents. The input
can be a generator, so don't rely on indexing, `len(documents)`, or visiting it a
second time.

### Work the supplied dataset by hand

The following are the raw scores for `termination notice`. Full contents are in
`examples.py`, in this deliberately inconvenient input order:

| ID | Score | Eligible for Alice at firm-a? |
|---|---:|---|
| z-private | 8 | No: restricted to Bob |
| y-foreign | 8 | No: belongs to firm-b, even though public |
| c | 2 | Yes |
| b | 4 | Yes |
| a | 4 | Yes |
| d | 0 | Readable, but has no matching tokens |

With no category filter and `limit=2`, the answer is:

```python
[
    SearchHit("a", "Termination letter", 4),
    SearchHit("b", "Termination policy", 4),
]
```

Why not `c`? It scores below a and b even though encountered first.
Why not z-private or y-foreign? A high score cannot override a permission failure.
Why a before b? The scores tie, so ascending document ID decides.
Why not d? `notices` is not the whole token `notice`.

**Apply the limit last.** Limiting globally before permissions, or stopping as soon
as you encounter two readable matches, both give incorrect results here.

Run the assembly tests, then the original contract:

```bash
python -m pytest -q tests/test_stages.py -k stage4 -x
python -m pytest -q tests/test_original_contract.py -x
```

The first command has 5 cases. The second has all 16 original V2 search cases,
with only their imports changed for this standalone folder.

Finally:

```bash
python -m pytest -q
python demo.py
```

Target: **47 passing tests** and the demo showing a (4), then b (4).

## After it works: an interviewer adds a requirement

Do this only after saving your working version. This is an **optional new contract**,
not a previously hidden requirement:

> Add a keyword-only `min_score: int = 1`. Results with scores below min_score are
> excluded. Values below 1 raise ValueError, including with empty inputs. All
> existing callers must keep working unchanged.

Use the supplied data and query `termination notice`:

```text
min_score=1 => a (4), b (4), c (2)
min_score=3 => a (4), b (4)
min_score=5 => []
min_score=0 => ValueError
```

Write these four tests in `tests/test_extension.py` **before** changing the
implementation. Also test `min_score=0` with empty data and an empty query.
Where should the new check live relative to ranking and limit? Explain it, then
implement it. Keep all 47 original guided tests passing.

## Architecture discussion — keep it connected to this code

A full scan is acceptable in this exercise. For the discussion, assume there are
2 million documents and many repeated searches.

An inverted index, in this simplified setting, is a mapping such as
`'notice' -> IDs of documents containing that term`. Think through how candidate
lookup might change without changing permissions or the scoring contract.

Explain what the current function rebuilds per request. Then describe one
improvement, not a complete platform. What updates become necessary when a
document's text changes, a user loses permission, or a category changes? Why would
caching results by query alone be wrong for Alice and Bob?

Discuss runtime in terms of corpus text examined, query words checked, and the
number of matching hits sorted. Do not describe the whole operation as only
`O(N log N)` while ignoring tokenizing text. No implementation is required here.

## Validation and provenance

This pack was checked using Python 3.13.5 and pytest 9.0.2. A separate temporary
reference implementation passed all 47 tests and the demo. That implementation
is **not included**. The starter was also checked: 3 setup tests pass and all 44
exercise cases fail intentionally. No timing thresholds or network services are
used by the tests. A fresh dependency download was not tested.

The record fields, tokenizer, public search contract, and 16 original search tests
come from Round 2 of `packs/v2/`. Changes: new helper
functions, helper tests, worked synthetic examples, this guide, and the explicitly
optional min_score extension. The earlier pack remains unchanged.

Python references for syntax, not search-product requirements:

- [Data structures: sets, membership, and intersections](https://docs.python.org/3.13/tutorial/datastructures.html)
- [Sorting with key functions](https://docs.python.org/3.13/howto/sorting.html)
- [Dataclass records](https://docs.python.org/3.13/library/dataclasses.html)
- [Built-in types: truth testing and frozen sets](https://docs.python.org/3.13/library/stdtypes.html)

**Start with Stage 1.** Read one small failing case, implement the helper, and
explain its output before moving to the next stage. Green tests are a checkpoint;
being able to explain why a result is correct is the goal.
