# Small architecture discussions after working code

Spend 5–10 minutes on one section after each coding round. Explore how the local
exercise would change with production workloads and operational constraints.

## 1. Search and permissions

Your scan works for hundreds of documents. Now suppose there are millions. Explain
what you would measure, what you would index, and what you would avoid loading per
request. Which filtering/ranking work can move into the retrieval engine? What is
the consequence of taking K results before filtering? How would index permissions
stay synchronized? Could cache keys or aggregate counts reveal inaccessible data?

## 2. A minimal ingestion path

Describe the responsibilities of a source connector, document-version store,
extraction/chunking worker, indexing layer, and query service. Name the source of
truth. Explain duplicates, retries, stale events, deletion, and the commit/publish
gap without saying “exactly once” as a substitute for a mechanism. What version
must an asynchronous result carry before it can safely be written back?

## 3. Chat grounded in retrieved documents

Where are permissions checked before content reaches a model? What metadata must
survive selection so references remain reviewable? What would you return with no
eligible context? How would you reject unknown citation labels? What distinguishes
source provenance from checking whether the answer is actually supported?

## 4. Latency and partial failure

Several retrieval sources have very different latency/error rates. Where is the
request-level deadline, compared with each source’s timeout? Would a partial answer
be distinguishable from a complete result? What happens when the client cancels?
How do you keep limits meaningful across processes? Which metrics tell you whether
you are constrained by CPU, upstream I/O, queue depth, or resource allocation?

## 5. When would FastAPI become relevant?

Only as a small adapter unless the interviewer asks for more: what belongs in input
validation and the handler, what belongs in a testable application function, and
what belongs in storage/retrieval? Where does trusted identity come from? What
should not be trusted just because it was supplied in a request header?

## Self-review

Can you state one concrete invariant for correctness, security, and reliability?
Can you explain the smallest improvement that addresses the stated new constraint?
Do you know what you intentionally left out? Prefer that over listing infrastructure
products. Do not build an elaborate platform before the local function works.
