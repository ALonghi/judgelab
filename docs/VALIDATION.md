# Delivery validation

## Private hosted deployment (2026-09-10)

Local suite: 38 app tests pass, including fail-closed hosted configuration,
authentication on pages/assets/data routes, malformed credentials, and retained
Host/Origin/CSRF checks. Fly.io deployment uses one Machine in Frankfurt with an
encrypted persistent volume. Anonymous HTTPS bootstrap returns 401; authenticated
homepage, bootstrap and indexed-lesson requests return 200 with all 32 activities.

On the deployed Python 3.13 image, the service user has UID 10001. The three
indexed-search reference checkpoints pass their 9, 13 and 7 cases through the
actual runner under that user. These probes did not import local learner progress
or record practice attempts. Login credentials and the short-lived deployment
token are excluded from Git and the image.

## Indexed-search extension (2026-09-10)

Validated on local CPython 3.14.7. The 32-activity catalog now has 19 coding
missions. All 19 full reference files pass their selected suites through the
application runner: 207 case executions, including overlapping guided tests.
Guided reveal snippets are intentionally not standalone modules; those checkpoints
were validated using the full shared reference file.

`python -m pytest -q tests_app`: 26 passed. Added coverage checks all three indexed
references and their deliberately failing starters, supporting schema visibility,
lesson ordering and a disk-index → ranked chunks → existing context-builder
integration, including reopening the database and permission revocation.

The new pack has 29 acceptance cases: 9 for incremental index construction,
13 for indexed scoring and 7 for chunking. Query checks reject body reads, count
rows crossing into Python and inspect term-index lookup plans. These verify
specific mechanisms, not an OOM stress test or million-document throughput claim.

The earlier delivery record below describes its original runtime and scope.

## Runtime

Validated in this environment using:

- CPython 3.13.5
- pytest 9.0.2
- pytest-asyncio 1.3.0
- FastAPI 0.128.2
- HTTPX 0.28.1
- Pydantic 2.13.4

The existing installed dependencies were used. A fresh online installation could
not be performed because outbound package-network access was unavailable.

## Exercise execution

All **16 coding activities** were run through the actual application test runner
using the newly authored reference approaches. All passed their complete selected
original test suites: **178 case executions**, including deliberate overlaps
between guided checkpoints and standalone acceptance suites. This is NOT a claim
that there are 178 distinct tests.

The four guided selections respectively execute 9, 7, 7 and 44 cases. Stage four
repeats prior stages and adds the original search contract. The setup-only tests
from the original packs are not learner acceptance tests in the UI.

Reference implementations are intentionally separate from the unchanged starters.
Running an unfinished starter is supposed to fail. New submission syntax errors,
skipped collections and timeouts are not mistaken for passes.

## App regression tests

`python -m pytest -q tests_app` completed with **17 passing tests**. Coverage includes:

- Catalog and original-source/test paths.
- Keeping quiz keys out of the initial UI payload.
- Stage-limited guided reference reveal.
- Actual pytest pass and failure runs.
- Syntax failure, skipped-suite rejection and process timeout.
- Exact submitted-code capture and fingerprint.
- Non-semantic interview cue behavior.
- Progress persistence and one-time XP awards.
- Serving the actual local HTTP assets and bootstrap.
- Host/origin/token restrictions, path traversal and consent checks.
- Quiz correction and local draft export.

These tests are not a security audit or an isolation proof.

## Browser/UI checks

The interface was rendered in headless Chromium through Playwright. Direct browser
navigation to localhost was blocked by this environment’s managed browser policy;
that policy was not changed. Instead a DOM harness loaded the real local HTML/CSS/JS
into a blank page and forwarded frontend API calls to the actual local Python server
through Python’s HTTP client. Thus test feedback came from real pytest, not mocked
passing results. Browser local storage was represented by an in-memory adapter in
the harness; server-side persistence was independently exercised.

Checked flows:

- Homepage and chapter navigation.
- Guided editor and original source rendering.
- Starter submission returning nine genuine failures.
- A real implementation returning 9/9 passes.
- Revealing only the current guided function.
- Preserving code into the next shared-file checkpoint.
- Wrong-answer correction and successful quick-check retry.
- Interview structure cues and rubric self-review.
- Answer persistence into a new page session using the real server state.
- Mobile overview without horizontal document overflow.

No JavaScript page errors occurred in those checks. Screenshots were visually
inspected. This is a DOM/API integration check, not a complete real-browser networking
or OS-launcher end-to-end test. Windows/macOS launchers and cross-browser clipboard
behaviour were not executed in this Linux environment.

## Limitations worth remembering

There is no LLM-based code review or semantic interview grading. Tests cover their
assertions only. This is a localhost tool for your own trusted code; submitted code
still has the operating-system permissions of the user running the server.
