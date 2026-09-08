# Delivery validation

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
