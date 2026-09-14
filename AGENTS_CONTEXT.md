# JudgeLab — Project Context for Coding Agents

## Purpose

JudgeLab is a public portfolio project and local Python playground for practising backend problem-solving and system-design reasoning.

The intended experience is closer to Duolingo / Typeform / an interactive coding coach than to a static collection of coding exercises.

The learner should be able to:

1. Read a realistic engineering problem.
2. Learn the concepts needed to solve it.
3. Write actual Python code.
4. Run real automated tests against that code.
5. See useful failure information.
6. Receive progressive hints instead of immediately seeing a solution.
7. Retry until the implementation is correct.
8. Reflect on architectural follow-up questions.
9. Practise interview-style explanations.
10. Build confidence through visible progress.

The project is deliberately focused on **realistic backend engineering work**, not competitive programming.

---

# Primary learner profile

The curriculum is suitable for readers with this general background:

- Software engineer with prior backend development experience.
- Strongest background is backend and distributed systems.
- Has worked with:
  - event-driven architecture,
  - messaging systems,
  - relational databases,
  - production-critical applications,
  - reliability engineering,
  - observability,
  - asynchronous workflows,
  - system design,
  - technical ownership,
  - mentoring,
  - stakeholder communication.
- Has meaningful experience in applied AI / LLM systems:
  - prompt engineering,
  - context engineering,
  - RAG,
  - structured outputs,
  - schema validation,
  - multiple model providers,
  - model routing,
  - retries,
  - idempotency,
  - cost tracking,
  - observability.
- Has worked in languages such as Scala, Rust, TypeScript, JavaScript, and Python.
- Python is **not necessarily the learner's strongest or most recent language**.
- Therefore, the product should help the learner express existing engineering judgment idiomatically in Python without assuming they are a beginner engineer.

This distinction is important:

> The learner may understand concurrency, distributed systems, APIs, databases, and reliability very well while still needing practice with Python syntax and idioms.

The app should therefore avoid patronizing explanations while still explaining Python-specific mechanics clearly.

---

# Practice session structure

A suggested session combines:

1. A short Python coding warm-up.
2. A progressively more involved exercise.
3. General software-engineering problem solving.
4. Architecture discussion related to the code.

Readers can consult syntax references and choose a separate architecture session
when they want to explore beyond the local implementation.

Because of this, JudgeLab should optimize for:

- clear reasoning,
- correctness,
- incremental changes,
- readable code,
- sensible data structures,
- handling edge cases,
- testing,
- API contracts,
- failure modes,
- performance awareness,
- maintainability,
- architectural discussion.

It should **not** optimize primarily for:

- obscure algorithms,
- dynamic-programming tricks,
- competitive-programming patterns,
- memorizing Python trivia,
- framework-specific trivia.

---

# Technical environment

Exercises should target:

```text
Python >= 3.13
```

The local application should be easy to run with a standard virtual environment.

Preferred workflow:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

or equivalent.

External infrastructure should not be required for the core course.

Prefer:

* in-memory repositories,
* fake network clients,
* synthetic document corpora,
* local pytest tests,
* deterministic fixtures.

Avoid requiring:

* cloud credentials,
* external databases,
* API keys,
* paid APIs,
* real LLM calls,
* Docker,
* Kubernetes,
* internet access after dependency installation.

---

# Domain used for exercises

The project uses a **document intelligence / knowledge search** domain because it creates realistic backend problems without requiring huge infrastructure.

The conceptual application works with collections of documents and may provide:

* document ingestion,
* document updates and deletion,
* classification metadata,
* keyword / text-based search,
* ranked search,
* relevance scoring,
* retrieval,
* RAG-style context construction,
* citations / references,
* conversational answers grounded in retrieved documents,
* tenant boundaries,
* access permissions,
* asynchronous indexing or enrichment,
* multiple retrieval sources.

This is only a practice domain.

Do not present the exercise implementation as a model of any specific real product.

---

# Core conceptual data model

Typical exercises may use data shaped like:

```python
@dataclass(frozen=True)
class Document:
    tenant_id: str
    document_id: str
    version: int
    title: str
    text: str
    categories: frozenset[str]
    allowed_users: frozenset[str]
    public: bool
```

Other exercises may introduce:

```python
@dataclass(frozen=True)
class SearchHit:
    document_id: str
    title: str
    score: int
```

or passages such as:

```python
@dataclass(frozen=True)
class Passage:
    document_id: str
    chunk_id: str
    text: str
    score: float
```

The exact model may evolve.

Important conceptual concerns include:

* identity,
* tenant isolation,
* permissions,
* document versions,
* stale updates,
* tombstones/deletes,
* ranking,
* limits,
* deterministic ordering,
* deduplication,
* partial failure,
* source provenance.

---

# Curriculum order and upload progression

The full ordered curriculum is recorded in docs/CURRICULUM.md. Use one canonical
lesson order in app/catalog.json for chapter lists, the home action and automatic
continuation. Home selects the first unfinished required activity; Continue selects
the next unfinished required activity after the current one, falling back to earlier
unfinished work. Neither path should prioritize a hard-coded chapter or optional
recap. After everything is complete, the review action returns to the start.

The seven chapters are Python data handling, APIs & document state, Search rules
& access, Indexes/full-text search/context, Reliability & async, Large uploads,
and Architecture. Start with sets and record-processing warm-ups. The API chapter
contains `p-fastapi`, `p-ingest`, `q-version`, `c-events` in that order: HTTP, local
idempotent updates, the local-counter/source-revision distinction, then out-of-order
source events. Keep those different version contracts explicit.

Interleave each search-rule quiz with its guided coding checkpoint. Then teach
manual index construction/query, built-in FTS, chunking and context. The optional
`c-search` recap remains available separately. In async, teach basic scheduling,
bounded fetching and cancellation before federated retrieval; stream parsing
precedes provider fallback. The final architecture sequence covers API ownership,
durable ingestion, large imports, search scale, latency and grounded answers.
Preserve every activity ID, workspace and acceptance contract when reordering.
Declare useful learning prerequisites in `depends`; each must appear earlier in
the path and must not depend on an optional recap. Activities remain freely openable.

The `uploads` chapter follows async reliability and contains `u-upload`, `u-batch`
and `u-extract` in `packs/uploads`. They implement resumable contiguous-offset
byte transfer, a fixed worker pool, and incremental UTF-8 line extraction. Supplied
local storage and a SQLite FTS5 revision transaction connect transfer/extraction
to actual search. The line extractor rejects lines over a configured limit; it is
not a PDF/OCR parser or a general solution for unbroken text. The adapter models
one immutable source and one writer; it does not implement cloud multipart
manifests or a crash-safe upload session. The batch report retains O(files) metadata.
Upload acceptance tests allow any positive read size up to `part_size` and compare
byte content, not object identity. Bound unacknowledged bytes rather than requiring one read per uploaded part.
Lost-reply and truncated-source checks must preserve acknowledged prefixes without
assuming a fixed part length or requiring incomplete buffered data to be uploaded.

`s-large-import` compares download-only storage with asynchronous full-text search
for a synthetic legal-records portal. Its 5-million-file tenant, low daily edit
rate, large imports and proposed 15-minute ordinary-text freshness target are
assumptions to validate. OCR needs a separate measured target. Revocation requires
prompt denial despite delayed index updates. Teach object/metadata reconciliation,
per-file status, capacity for initial imports/rebuilds, tenant fairness and current
access on snippets/downloads. Production staging, durable jobs and permission
checks are architecture discussion; the trusted local demo does not implement
those services. Preserve these distinctions in teaching copy and tests.

# Existing exercise themes

The course was designed around several groups of exercises.

## 1. Python warm-ups

Warm-ups should be small but realistic.

Examples:

* select the latest document version,
* aggregate classification labels,
* transform records,
* deduplicate values while preserving required semantics,
* sort records by several criteria,
* work with dictionaries and sets.

Warm-ups exist to help the learner become comfortable writing Python under observation.

They should not be toy exercises like:

```text
reverse a string
```

unless the concept genuinely supports later work.

---

# 2. Ranked document search

A core guided exercise implements a simplified document search function.

A representative scoring rule is:

* each distinct query term appearing in the title contributes 3 points,
* each distinct query term appearing in the body contributes 1 point,
* a term may score in both places,
* repeated occurrences do not add extra score,
* partial query matches are allowed.

Example:

```text
Query:
termination notice

Title:
Termination clause

Body:
Notice of termination.
```

Score:

```text
termination:
    title = 3
    body  = 1

notice:
    title = 0
    body  = 1

total = 5
```

This teaches:

* tokenization,
* sets,
* membership checks,
* loops,
* scoring,
* deterministic sorting,
* filtering,
* limits.

---

# 3. Permissions and tenant boundaries

Search must not leak inaccessible documents.

A useful conceptual rule is:

```text
different tenant
    -> always reject

same tenant + public
    -> readable

same tenant + private + user explicitly allowed
    -> readable

same tenant + private + user not allowed
    -> reject
```

A highly relevant inaccessible document must remain invisible.

One important interview lesson is that filtering order matters.

Bad approach:

```text
1. Rank globally.
2. Take top N.
3. Remove documents the user cannot access.
```

This can return fewer results than requested and can have serious security implications.

Preferred conceptual flow:

```text
1. Determine eligibility.
2. Score eligible documents.
3. Sort eligible results.
4. Apply result limit.
```

In real systems, access control may need to be enforced deeper than the HTTP/controller layer.

---

# 4. Category / classification filtering

Documents may already contain category labels.

The exercises do **not** require building a classifier.

Example semantics:

```python
categories = None
```

means:

```text
no category restriction
```

while:

```python
categories = frozenset()
```

may intentionally mean:

```text
match nothing
```

and:

```python
frozenset({"contract", "memo"})
```

may mean:

```text
document must contain at least one requested category
```

This is useful for teaching the difference between:

```python
None
```

and:

```python
empty collection
```

and for practising set intersections.

---

# 5. Context construction / RAG preparation

The core chapter now teaches a disk-backed retrieval bridge before context:
`c-index-build` writes per-term postings to SQLite while consuming units once;
`c-index-query` scores with stored weights and applies the result limit in SQL;
`c-chunking` yields identified chunks that the same index/query can retrieve.
The context quiz follows those checkpoints, then `c-context` consumes their
ranked text. The source revision quiz sits before event ingestion; cancellation
follows basic async fetching. Preserve activity IDs when changing their order so
saved work and progress remain associated with the original activities.

`c-search` is an optional independent recap of `g-search`, which already runs
the same acceptance contract. Preserve its ID, workspace and saved progress, but
exclude optional activities from chapter numbering, chapter completion and
automatic continuation. Keep recaps accessible from their chapter and Code arena.
The required index chapter starts with index construction after guided search;
category counts now belong to the earlier Python data-handling chapter.

`c-fts` follows the manual index-query checkpoint with a real SQLite FTS5 query
exercise in `packs/fts`. The caller selects one customer's database. Setup and
query-word preparation are supplied; the learner implements MATCH, user-access
filtering, ascending default rank and SQL LIMIT. Its all-word matching and BM25
ranking differ deliberately from the manual index's OR matching and 3/1 points.
Keep the two contracts separate. The FTS demo shows edits, deletion and reopening
the database without requiring a search service or any external credentials.

The indexed pack uses local SQLite files and synthetic data, without an external
service. Distinguish source buffering, result buffering and query scan cost.
Never equate a generator with indexed retrieval, an in-memory postings dictionary
with bounded memory, or a SQL LIMIT with bounded total database work. These
exercises retain the toy title/body score, not BM25. Document construction still
holds one source body; huge individual files need a separate streaming extractor.
The uploads pack now provides one for bounded UTF-8 lines; it does not parse PDFs or perform OCR.

The project should teach the application logic around retrieval-augmented generation without requiring actual LLM API calls.

Example problem:

Given already-ranked passages:

```text
A: 3 words
B: 10 words
C: 2 words
```

and a context budget of 5 words:

```text
include A
skip B
include C
```

The implementation may need to:

* preserve relevance order,
* respect a context budget,
* remove duplicates,
* skip inaccessible sources,
* limit chunks per document,
* preserve provenance,
* create stable reference labels.

Example output conceptually:

```text
[1] passage from document A
[2] passage from document C
```

with source metadata:

```python
{
    1: {"document_id": "...", "chunk_id": "..."},
    2: {"document_id": "...", "chunk_id": "..."},
}
```

Important lesson:

> The source mapping must remain correct even after filtering, deduplication, or skipping oversized passages.

---

# 6. Document ingestion and versioning

Another major exercise deals with events arriving out of order.

Example:

```text
upsert version 1
delete version 5
delayed upsert version 3
```

Expected:

```text
document remains deleted
```

Then:

```text
upsert version 6
```

may restore the document depending on the exercise contract.

Topics include:

* idempotency,
* versions,
* stale events,
* duplicate events,
* tombstones,
* event ordering,
* composite document identity,
* concurrent writers.

Possible PostgreSQL follow-ups:

* unique constraints,
* `INSERT ... ON CONFLICT`,
* transactions,
* race conditions,
* optimistic concurrency.

---

# 7. Async / concurrent retrieval

Concurrency is useful practice but should not dominate the course.

Representative exercise:

```text
Fetch multiple documents concurrently.

Requirements:
- maximum N requests in flight,
- timeout each request,
- preserve input order,
- duplicate IDs result in one downstream request,
- one failure must not fail the entire operation.
```

Useful Python concepts:

```python
async def
await
asyncio.gather
asyncio.create_task
asyncio.Semaphore
asyncio.Queue
asyncio.timeout
```

Follow-up concerns:

* creating too many tasks,
* global versus process-local concurrency,
* retries,
* rate limiting,
* cancellation,
* partial failures.

The learner already understands concurrency conceptually, so the emphasis is on translating those concepts correctly into Python.

---

# 8. Streaming / conversational output

The application domain may contain chat-like functionality.

Practice can include consuming or producing streams without requiring a real language model.

One example:

* receive chunks asynchronously,
* do not buffer the entire response,
* handle timeout between chunks,
* preserve partial-output semantics,
* propagate cancellation,
* optionally fall back to another provider only when it is safe.

A useful rule:

```text
If primary fails before producing output:
    fallback may be possible.

If primary already produced visible output:
    silently switching provider may create incoherent output.
```

Another useful exercise is parsing logical messages that arrive split across arbitrary network chunks.

---

# 9. Bad-code debugging exercises

Some exercises intentionally start from flawed code.

Examples of deliberate problems:

```python
time.sleep(...)
```

inside:

```python
async def
```

or:

```python
def f(items=[]):
```

or:

```python
except Exception:
    pass
```

or:

* serial awaits that should be concurrent,
* unbounded concurrency,
* shared mutable process-local state,
* missing cleanup,
* incorrect tenant filtering,
* filtering after applying limits.

The learner should:

1. identify the problem,
2. explain why it matters,
3. improve it,
4. preserve required behavior,
5. run tests.

---

# Pedagogical philosophy

JudgeLab should not simply provide a problem statement and say:

```text
Implement this.
```

Guided exercises should help readers build confidence with unfamiliar material.

Each guided exercise should therefore ideally contain:

1. Context.
2. A concrete example.
3. Explanation of the relevant Python feature.
4. A small implementation task.
5. Tests for that stage.
6. Progressive hints.
7. Edge cases.
8. A more difficult integration step.
9. Architecture follow-ups.

The difficulty should increase progressively.

Every activity starts with a self-contained problem and its agreed requirements
(`scenario`). Make it as descriptive as the learner needs to understand the
situation, constraints and expected outcome. Prefer ordinary, precise words.
Length is not a quality target: remove filler, but do not remove context merely
to meet a word count. Do not frame definitions or general design alternatives as
things the interviewer said. Keep definitions, Python notes, alternative designs
and related lessons in the separate Knowledge base view. Keep concrete examples
and implementation guidance in Walkthrough. The learner can move directly to
Practice or consult either learning view first. Preserve detailed teaching
without forcing it into one uninterrupted page before the task.

Teach transfer beyond the exercise throughout the learning path. Each activity's
`strategy` field must name and explain the engineering approach, give a realistic
use case, and connect an illustrative interview problem to the constraints that
would make the approach appropriate. Include how to propose it, limitations and
alternatives. These are practice scenarios, never claims about actual interview
questions. Distinguish simplified exercise contracts from production decisions
(for example, word budgets from model token budgets, greedy heuristics from
optimal selection, and local version counters from source revisions). Use
progressive disclosure for deeper reasoning while keeping the strategy and
problem it addresses visible before the exercise.

The learning sequence is Problem → Walkthrough → Practice, with Knowledge base
available separately throughout. Problem contains the situation, constraints and
expected outcome, not a glossary or solution. Walkthrough starts with the real
system in which the concept appears, then explains the approach at a high level:
what triggers it, which component owns it, what state it retains and how reads
and writes use that state. Follow with a concrete worked example, then the bounded
exercise implementation.

Ground every topic in a credible use case. For each design, cover the system
properties that would change the decision. These may include the source of truth,
derived state, read and write paths, freshness, recovery or workload. Select the
relevant concerns instead of forcing every category into every lesson. Explain a
production direction and at least one reason to choose differently. State which
part the exercise models and which parts it omits. A simplified implementation
should expose a useful mechanism or decision; its simplicity is not evidence that
teams should deploy it unchanged.

Open an architecture explanation with a concrete situation. For an existing
system, name the observed failure or new requirement and the evidence that points
to it. For a new system, state expected scale and behavior as assumptions that
will need measurement later. Do not open with a generic checklist of metrics.
Introduce an unfamiliar term by first describing the operation it names. When
comparing designs, give a concrete condition for choosing each one. Avoid phrases
such as “use an appropriate engine” that merely rename the decision.

Mention omitted production work only when it prevents a false conclusion about
the exercise. Say plainly whether the current course covers that work. Do not
send the learner toward a later activity unless it implements the missing part.

For derived state such as indexes or caches, explain what populates it and how
updates/deletions reach it, distinguishing implemented behavior from production
extensions. Introduce storage and freshness trade-offs before schema or API
instructions. Explicitly map educational implementations to production choices;
do not present hand-built exercise internals as default production
recommendations. Keep query work, process memory, storage layout, write
amplification and operational complexity distinct.
Use a connected flowchart when several components, states or branches are easier
to understand spatially than in short prose. Reuse a named diagram when lessons
share the same flow. Keep simple functions in prose. Diagrams must show meaningful
connections such as shared storage, branch outcomes or async boundaries, rather
than decorating a row of cards with arrows. Use expandable supporting detail and
responsive layouts to avoid a single uninterrupted column of text.
Use practical values, records, requests and failure cases. Avoid repeated setup,
generic numbered chapter headings and instructional filler. The `problem` field
continues to hold worked reasoning; `scenario` is the interview-facing brief. It
may be detailed when the details affect the design or remove ambiguity.

An approach description must explain execution, not just name a pattern. Each
activity's `implementation` field states the data/state to retain, ordered
operations, and a verifiable outcome. Every displayed clarification question
must explain how plausible answers change the design. Distinguish prerequisites
from supplied assumptions and link related lessons with a precise account of
what they teach and what they do not. Use small executable teaching examples and
state traces where useful; keep learner files and gated reference solutions
separate. Do not imply later exercises cover missing material without checking.

Read the rendered lesson in sequence when reviewing teaching copy. Before each
design question or alternative, explain the concrete situation and introduce the
terms it refers to in connected prose (`decisions[].lead_in`). A glossary entry
alone is not a narrative introduction. Do not make readers infer an unstated
pipeline stage or present an already-fixed exercise assumption as an open question.

Example:

```text
Stage 1:
score one document

Stage 2:
check access

Stage 3:
check categories

Stage 4:
assemble complete search

Extension:
add a new requirement without breaking existing behavior
```

This is more useful than immediately asking the learner to build an entire search service.

---

# Hints philosophy

Hints should be progressive.

Example:

### Hint 1

Point toward the concept:

```text
You need to know whether two sets share at least one value.
```

### Hint 2

Point toward a Python operation:

```python
a & b
```

### Hint 3

Show a similar example without solving the exact exercise.

The final reference solution should only become available after the learner has attempted the problem.

Avoid giving the completed implementation immediately.

---

# Validation philosophy

Coding exercises must execute actual code.

A solution should pass only when the real tests pass. Show each activity's tested
functions and test count before submission and beside feedback. Shared files can
contain later stages: passing one selected stage validates only that stage. Link
the other activities sharing that file so learners can validate work done ahead.
The final guided-search stage validates all helpers and full search integration.

Do not simulate success using text comparison.

The runner should distinguish:

* passing tests,
* assertion failures,
* syntax errors,
* import errors,
* timeouts,
* no tests collected,
* crashes.

The feedback should expose useful information from pytest while avoiding overwhelming the learner.

---

# Testing philosophy

Tests should include more than happy paths.

Useful cases:

* empty input,
* duplicate records,
* wrong tenant,
* restricted documents,
* equal scores,
* deterministic tie-breaking,
* invalid limits,
* invalid parameters,
* stale events,
* repeated events,
* partial failures,
* timeouts,
* cancellation where relevant,
* one-pass iterables,
* caller input not mutated.

Tests should reveal common mistakes.

Example:

If the correct search order is:

```text
A = inaccessible, score 20
B = accessible, score 15
C = accessible, score 10
```

and:

```text
limit = 2
```

correct result:

```text
B, C
```

A test like this catches:

```text
rank -> limit -> permissions
```

when the intended semantics are:

```text
permissions -> rank -> limit
```

---

# Architecture discussion mode

The six architecture activities extend the coding exercises with design questions.
They use written answers, keyword cues, self-review rubrics and follow-up prompts.
These checks do not evaluate semantic correctness.

Interview Studio and the personal-experience chapter have been removed. Keep the
coding chapters and architecture chapter under Your Chapters. New discussion
activities should focus on systems, constraints, trade-offs and failure handling.

---

# Product UX

The intended UI is inspired by:

* Duolingo,
* Typeform,
* interactive coding platforms.

Desired characteristics:

* one focused task at a time,
* obvious progress,
* visible completion,
* low cognitive clutter,
* immediate feedback,
* rewarding but not childish,
* easy retry loop.

Existing concepts include:

* XP,
* progress tracking,
* bookmarks,
* retry queue,
* lesson groups,
* guided mode,
* challenge mode,
* code editor,
* test result panel,
* hints,
* reference approach,
* architecture discussion,
* practice timers.

Do not turn the application into a giant dashboard full of metrics.

The primary loop should remain:

```text
learn
→ attempt
→ run
→ inspect
→ fix
→ pass
→ continue
```

---

# Code editor expectations

The editor should support basic features such as:

* Python syntax highlighting,
* readable monospace font,
* comfortable indentation,
* preserving the learner's work,
* run-tests action,
* reset/retry,
* optional export.

Keep supplied model fields, types and defaults accessible beside the filename,
with the reference visible above the editor. Include models declared in learner
starter files as well as shared model modules. Offer local name, field and common
Python method completion with a clickable control and Mac-aware shortcut labels.
Preserve Command-Space and Option-Space for the learner’s OS tools. Completion
must describe its limits honestly and draw only on supplied scaffolding and
standard Python vocabulary, keeping reference solutions gated.

A full IDE is not necessary.

Avoid adding features that distract from interview practice.

---

# Progress model

Progress should be stored locally.

Possible values:

```text
not_started
attempted
completed
```

Track useful information such as:

* attempts,
* completion state,
* XP awarded,
* bookmarks,
* current code,
* hints revealed.

Do not punish failed attempts with artificial lives or lockouts.

The intended psychology is:

> retrying is part of learning.

---

# XP / gamification

Gamification exists to encourage continued practice.

It should remain secondary to learning.

Good uses:

* XP for first completion,
* visible lesson progress,
* streak-like optional motivation,
* completion animations,
* badges for groups of skills.

Avoid:

* making users afraid to attempt difficult problems,
* subtracting points for failure,
* rewarding rapid guessing,
* turning interview preparation into a grind mechanic.

---

# Architecture discussion

A coding exercise should often lead into a short system-design conversation.

Example:

After implementing in-memory document search, ask:

```text
What changes if there are 10 million documents?
```

Possible areas to discuss:

* search indexes,
* inverted indexes,
* database search,
* dedicated search engines,
* vector indexes,
* pagination,
* caches,
* permissions,
* consistency.

After ingestion:

```text
What happens with multiple workers?
```

Possible areas:

* transactions,
* optimistic locking,
* event ordering,
* idempotency,
* queues.

After async retrieval:

```text
What happens across 20 service replicas?
```

Possible areas:

* distributed rate limits,
* shared queues,
* global concurrency,
* backpressure.

The application should not require one universally "correct" architecture.

Instead, the learner should explain trade-offs.

---

# Python style goals

The learner should practise writing idiomatic, understandable Python.

Useful constructs include:

```python
dict
set
frozenset
list
tuple

enumerate
zip
sorted
min
max
any
all

collections.defaultdict
collections.Counter
collections.deque

dataclasses.dataclass

asyncio
```

Encourage:

* straightforward loops,
* clear names,
* early returns,
* small functions,
* explicit contracts,
* sensible typing.

Discourage premature abstraction.

A particularly important coaching principle:

> Do not write Scala in Python.

The learner has experience with strongly typed / functional languages and may naturally over-abstract.

The interview goal is usually better served by:

```text
simple correct Python
→ tests
→ refactor when justified
```

rather than:

```text
interfaces
→ generic repository abstraction
→ domain service
→ strategy pattern
→ eventually solve the problem
```

---

# How the learner should narrate coding

Useful narration focuses on decisions.

Good:

```text
I'll first make the behavior correct, then check whether the input size
requires a more memory-efficient approach.
```

Good:

```text
I'll filter inaccessible documents before applying the limit because otherwise
we may return fewer than the requested number of eligible results.
```

Good:

```text
I'm using a dictionary keyed by document ID so lookup is constant-time and
duplicate events naturally address the same state.
```

Less useful:

```text
Now I'm creating a dictionary.
Now I'm writing a for loop.
Now I'm adding one.
```

The application may provide reminders about this in interview simulation mode.

---

# System-design scope

The deeper system-design interview is conceptually separate from live coding.

JudgeLab can contain architecture material, but coding exercises should not require the learner to design an entire production platform before writing code.

A sensible split is:

### During coding

Discuss:

* interfaces,
* state,
* data structures,
* error behavior,
* testability,
* complexity,
* immediate scaling issues.

### During architecture practice

Explore:

* services,
* queues,
* storage,
* indexing,
* caching,
* observability,
* security,
* deployment,
* failure recovery,
* scaling,
* data consistency.

---

# Privacy / multi-tenancy themes

Because the practice domain involves private document repositories, security boundaries matter.

Exercises should reinforce:

```text
tenant isolation is part of correctness
```

rather than treating it as an afterthought.

Useful questions:

* Where is tenant identity derived?
* Which layer enforces access?
* Can cached data cross tenant boundaries?
* Can ranking reveal that an inaccessible document exists?
* How are permissions updated?
* What happens when access is revoked?
* Can stale indexes expose removed content?

Do not turn every exercise into a security challenge, but these concerns should appear naturally.

---

# Observability themes

Architecture follow-ups may cover:

* structured logs,
* request IDs,
* trace IDs,
* latency distributions,
* error rate,
* timeout rate,
* queue depth,
* retries,
* cache hit rate,
* model/provider usage,
* token/cost usage,
* ingestion lag,
* indexing lag.

The learner has prior production experience, so these questions can be sophisticated.

---

# AI / LLM practice philosophy

AI-related exercises should focus on engineering around models rather than pretending the learner needs to implement a foundation model.

Useful topics:

* retrieval,
* context selection,
* citations,
* structured output,
* schema validation,
* retries,
* provider fallback,
* prompt versioning,
* provenance,
* observability,
* cost,
* deterministic application logic around probabilistic components.

Avoid requiring real LLM APIs in the core course.

---

# FastAPI

FastAPI may be included as an optional backend framework exercise because it is a common modern Python web framework.

However, the project should **not** assume that framework syntax is the central interview criterion.

Useful FastAPI practice may include:

* path/query/header parameters,
* Pydantic request/response models,
* validation,
* dependency injection,
* HTTP status semantics,
* test clients,
* repository/service boundaries.

Framework trivia should remain secondary to software-engineering reasoning.

---

# Public-repository privacy rules

This repository may be public.

Do not include:

* names of employers involved in an active hiring process,
* interviewer names,
* recruiter names,
* private recruiting emails,
* private scheduling links,
* salary negotiation details,
* confidential interview information,
* speculation presented as leaked interview questions,
* identifying information from the learner's CV,
* private contact information.

When discussing the origin of the project, use generic phrasing such as:

```text
JudgeLab is a public Python playground for practical backend exercises and
architecture discussions.
```

Do not imply that any exercise is a real question from a specific employer.

Use labels such as:

```text
domain-inspired exercise
realistic practice scenario
backend interview simulation
```

rather than:

```text
actual interview question
company interview question
```

unless that information is genuinely public and intentionally added later.

---

# Non-goals

JudgeLab is not intended to be:

* a competitive-programming platform,
* a complete Python course for first-time programmers,
* a production security sandbox,
* a replacement for a full IDE,
* a real document-management product,
* a real legal-search engine,
* a real LLM/RAG production system,
* an authoritative interview-question database,
* an employer-specific preparation leak.

---

# Security warning for local code execution

An explicitly requested private Fly.io deployment is now supported. The default
mode stays loopback-only. Hosted mode requires an HTTPS origin and a strong
password before binding externally; all content/API routes require authentication,
with Host/Origin/CSRF checks retained. It is single-user trusted-code execution,
not a public or multi-tenant sandbox. Deploy one unprivileged app process with a
persistent volume; exclude local progress and secrets from the build context.
See docs/HOSTING.md. The earlier prohibitions on public exposure still apply to
unauthenticated deployment and untrusted code submission.

Submitted Python code executes locally using the user's environment.

The application is not a hardened sandbox.

Therefore:

* bind the server to localhost by default,
* clearly document the risk,
* do not expose it publicly,
* only run trusted learner-authored code,
* do not describe the execution environment as secure isolation unless true OS/container sandboxing is added.

A UI message such as this is appropriate:

```text
Your submitted Python runs locally with your user permissions.
Only execute code you trust.
```

---

# Validation requirements for coding agents

When modifying JudgeLab:

1. Existing passing exercises must remain passing.
2. Exercise starter states should remain intentionally incomplete.
3. Reference solutions should pass all exercise tests.
4. Starter implementations should fail meaningful tests.
5. Syntax/import failures must not be interpreted as success.
6. Timeouts must be handled.
7. Zero collected tests must not count as success.
8. Test output presented to the learner should remain readable.
9. Do not accidentally expose reference solutions before the learner requests them.
10. Preserve saved learner work whenever possible.

---

# How to add a good new exercise

A strong exercise should have:

## 1. Clear engineering objective

Example:

```text
Merge ranked results from multiple search sources.
```

## 2. Concrete contract

Specify:

* input,
* output,
* errors,
* ordering,
* edge cases.

## 3. Starter implementation

Leave meaningful TODOs.

## 4. Tests

Include:

* happy path,
* at least several edge cases,
* common incorrect approaches.

## 5. Progressive hints

Do not reveal the solution immediately.

## 6. Architecture questions

Example:

```text
How would this work across several service instances?
```

## 7. Reference implementation

Keep it separate from learner code.

---

# Exercise quality bar

Avoid exercises that can be solved by blindly copying one obvious line.

A useful challenge should require several decisions.

However, difficulty should come from engineering reasoning, not trick wording.

Good difficulty:

* multiple requirements interact,
* ordering matters,
* stale events exist,
* permissions interact with ranking,
* failures are partial,
* state must remain consistent.

Bad difficulty:

* obscure language tricks,
* hidden assumptions,
* surprising Python behavior with no pedagogical purpose,
* puzzles unrelated to backend engineering.

---

# Recommended future curriculum

Possible future additions:

## Python fluency

* generators,
* iterators,
* context managers,
* decorators,
* typing,
* protocols,
* dataclasses,
* exception design.

## Data layer

* SQLite/PostgreSQL exercises,
* transactions,
* isolation,
* indexes,
* query planning,
* pagination.

## Backend APIs

* FastAPI service,
* authentication abstractions,
* validation,
* error mapping,
* idempotency keys.

## Search

* inverted index,
* BM25-inspired simplified scoring,
* pagination,
* merging keyword and semantic results,
* deduplication.

## RAG

* chunking,
* context budgets,
* citation mapping,
* retrieval evaluation,
* reranking.

## Concurrency

* bounded fan-out,
* worker pools,
* backpressure,
* graceful shutdown,
* cancellation.

## System design

* document ingestion pipeline,
* search platform,
* chat-with-documents architecture,
* multi-tenant indexing,
* synchronization with external document systems.

## Production debugging

* latency regression,
* dead-letter queue growth,
* stale permissions,
* failed indexing,
* duplicate events,
* downstream rate limiting.

---

# Guiding principle

The most important product principle is:

> JudgeLab should make an experienced engineer better at demonstrating their
> engineering ability under interview conditions.

That means the application should prioritize:

```text
understanding
+ implementation
+ feedback
+ iteration
+ explanation
```

over:

```text
memorization
+ trivia
+ arbitrary puzzle difficulty
```

Whenever a proposed feature conflicts with that goal, prefer the simpler feature
that increases the amount of deliberate practice.
