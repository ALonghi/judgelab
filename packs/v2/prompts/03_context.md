# Round 3 — turn retrieval results into bounded context with references

**Timebox: 25–35 minutes.** Implement `practice/round03_context.py`.
Run `python -m pytest -q tests/test_03_context.py -x`.

A chat application receives an already-ranked stream of text chunks. Select whole
chunks for the next model call, then construct deterministic citation labels.
**You do not implement or call an LLM.**

## Inputs and rules

Use the same tenant/user visibility rule as Round 2. Filter before deduplication
and selection. Skip blank content. Consider the first visible, nonblank occurrence
of each `(tenant_id, document_id, chunk_id)` only. Later duplicates do not replace
it, even if that first occurrence was too big for the budget.

Walk in rank order, including at most `max_per_document` chunks for each document.
Cost is whitespace-separated WORDS (`text.split()`), not model tokens. Include
only whole chunks. Skip an oversized chunk and try the next; do not stop searching
for smaller chunks that might fit. Cap counts only selected chunks.

Normalize selected content to single spaces. Assign labels `[1]`, `[2]`, ... only
after selection, without gaps. Join lines as `[n] content` with one newline. Return
`Context(text, tuple_of_citations, words_used)`. Each citation records its label,
document_id, and chunk_id. Labels/newlines cost nothing in this toy budget.

Example, budget=5:

- d1/c1: `one two three` -> include (3).
- d2/c1: `far too many words here` -> skip (5 would exceed remaining 2).
- d3/c1: `four five` -> include (2).

Result text: `[1] one two three\n[2] four five`; citations point to d1/c1 and d3/c1.

Validate word_budget >= 0 and max_per_document >= 1 before consuming input.
Budget zero and no eligible chunks both return `Context("", (), 0)`.

## Discuss afterward

Which parts belong in retrieval and which in prompt construction? How would a real
tokenizer, document versions, snippets, changing permissions, and model output
citations affect the design? What happens when the model cites a label never
provided? Why is a resolvable citation not proof the cited text supports a claim?

## Input and memory boundary

The input contains ranked, already-extracted text chunks, not raw files or network
fragments. The word budget bounds selected text. Deduplication retains identities
of all visible nonempty chunks inspected, including those skipped for size, so
its memory can grow beyond the selected output. The caller should bound incoming
chunk sizes and retrieval volume. Access fields belong to this function's input
contract; they do not prescribe storing a separate permission list per chunk.
