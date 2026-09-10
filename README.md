# JudgeLab

**A Python playground for building, testing and explaining backend systems.**

A public portfolio project and local, single-user learning app. Work through guided
lessons in a browser editor, run real pytest checks, and explore search, ingestion,
async workflows and API design. Includes progressive hints, reference solutions,
XP, a review queue and engineering discussion prompts.

## Start here

You need **Python 3.13 or newer**. The first dependency installation requires
internet access. Once installed, the app needs no internet, account or API key.
No Node.js, Docker, database or model service is required.

### macOS / Linux

Clone the repository, open a terminal in the `judgelab` folder, and run:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py
```

The app attempts to open your browser automatically. If it does not, open:

```text
http://127.0.0.1:8765
```

A Python 3.14+ interpreter also works with the code’s stated requirements, but
this delivery was tested on Python 3.13.5. Use your interpreter’s actual command
when creating the environment. Newer versions have not all been tested.

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

These commands do not require changing PowerShell’s script execution policy.

### Convenience launchers

`start.sh` on macOS/Linux and `start.bat` on Windows can create the environment,
install missing dependencies, and launch the app. They are convenience wrappers
around the commands above. The explicit commands are easiest to troubleshoot.

On subsequent visits, activate the same environment and run `python run.py`.
Keep the terminal running while practising. **Ctrl+C stops the app**.
Opening `web/index.html` directly will not execute Python; use the local server.

## What you can play

| Mode | Activities | What is validated |
|---|---:|---|
| Quick checks | 8 | Fixed answer keys and explanations of the practice contracts |
| Coding missions | 19 | Real pytest acceptance cases, run against your submitted Python |
| Architecture discussions | 5 | Word/keyword structure cues, followed by YOUR visible rubric self-review |

The six chapters are:

1. **Python, without the fog:** five checks on sets, scoring, tenant boundaries,
   filters and top-K ordering.
2. **Build your first search engine:** four guided checkpoints sharing one file.
3. **The backend coding path:** latest versions, category counts, unassisted
   search, disk-backed indexing, indexed scoring, chunking, context selection and
   revision-aware ingestion. Context/version quizzes sit beside their topics.
4. **Reliability & async lab:** refactoring, bounded fetching, cancellation,
   federated search, incremental stream parsing and LLM-style fallback.
5. **FastAPI & backend extras:** the original endpoint and idempotent ingestion.
6. **Think beyond the function:** five architecture discussions from V2.

### A good first session

The scalable-search continuation is **full-scan search → build an index on disk →
query posting weights with a SQL result limit → create searchable chunks → select
cited context**. See [the indexed pack](packs/indexed/README.md) for the schema,
SQL primer, exact contracts and runnable demo. The earlier scan is a correctness
baseline: streaming input can reduce source buffering but does not eliminate
per-query scanning or accumulation of all matching hits. The indexed pack does
not claim a million-document benchmark; it checks bounded Python result transfer,
indexed lookups, persistence and the connection to context construction.


Choose **Start guided search** on the homepage.

Read **Understand**, open **Write code**, and change `score_document` only.
Click **Run tests** (or **Ctrl+Enter / Cmd+Enter** in the editor). The first run asks
you to acknowledge that this executes code locally.

If a case fails, open it under **Test feedback**. You will see the real assertion,
a rule-based coaching cue, and the raw pytest output. Correct your code and rerun.
Hints appear one at a time. After at least one submission, **Compare a reference
approach** shows one working solution without replacing your work.

Continue to permissions, categories and full search. The earlier functions remain
in the same shared file. Stage four reruns all guided stages plus the original
standalone search acceptance tests.

### Coding editor

- Syntax highlighting, line numbers, four-space indentation and bracket matching.
- No AI completion. Tab inserts spaces; Shift+Tab reduces indentation.
- **Jump to target** locates the function for the current task.
- **Models & test source** shows the exact supporting records and assertions.
- **Focus mode** expands the editor.
- **Export .py** saves your current file for an IDE.
- **Reset** resets the ENTIRE shared file, with confirmation. Export first to
  preserve earlier functions. Completion badges remain past achievements.
- The optional timer never auto-submits or fails your work.

A test result describes the last submitted code. Editing it does not rerun tests.
When the current draft differs from that submission, the feedback is marked stale.

### Architecture self-review

The app is **not connected to an LLM**. It does not grade your answer’s factual
accuracy, semantic quality, seniority or production readiness.

It reports word count, estimated speaking time at 135 words/minute, and whether
certain cue words occur. These are only review prompts: a strong answer might not
use those words, and a weak answer might contain all of them.

You mark each rubric point **Covered** or **Needs another pass**. Finishing that
review earns rehearsal XP, NOT a “correct answer” badge. Items needing revision
go into the review queue. There is no microphone recording or transcription;
speak aloud and type a transcript or summary.

Discussion notes offer general speaking outlines. Use your own examples and
measurements when describing experience.

## Original contracts stay separate

The packs intentionally contain different exercises. Do not reconcile them into
one rule by accident:

- **V1 API search** is case-insensitive substring matching, with insertion order.
- **V2/guided search** is whole-token scoring, permissions and deterministic ranking.
- **V1 ingestion** uses a local version counter incremented when content/source changes.
- **V2 ingestion** compares source revisions, stores tombstones, and detects conflicts.
- **Warm-up equal versions** use the last payload, whereas equal conflicting
  revisions in V2 ingestion raise an error.

Every activity names its original pack. Exercise assertions define each pack’s contract.
New teaching prose, quick checks, reference implementations and self-review rubrics
are part of the playground.

## Your progress and privacy

Drafts, answers, last results, achievements, bookmarks and review points are stored
in `.judgelab/progress.json` on your machine. Browser local storage provides an
additional draft backup. There are no trackers, analytics or external API calls.

Use **Your lab → Export progress** to get a portable JSON backup. Import replaces
current progress, so export first. Import restores drafts, answers, achievements,
bookmarks and attempt counts; detailed old test results/review history are not
restored. Rerun tests to validate imported code.

XP is awarded once per activity. Repeating a pass does not farm extra XP. Completed
badges are historical, so they remain if you later experiment with your code.
The daily rhythm counts attempts, not distinct activities, and resets by local day.
No artificial locks or lost lives prevent practice.

Do not put real client documents, secrets or credentials in your submissions.
Exports contain your code and personal answer text; store and share them carefully.

## Safety: read before executing code

**This is not a security sandbox.** The Python you submit runs with your own account’s
permissions. A fresh working directory, subprocess and timeout do not stop code
from reading files, making network requests or running other programs.

Only submit your own trusted practice code. Do not paste unknown programs. Do not
expose this server to other users, bind it to a network interface, forward its port,
or deploy it to public hosting.

The server binds to `127.0.0.1` only and checks Host, Origin and a session token on
write requests. Test execution has a 20-second process deadline and a 256 KB console
output cap. It attempts process-tree cleanup; OS behaviours vary. These are local
practice safeguards, not a defense against a malicious contestant.

The standard-library HTTP server is deliberately a local development server, not a
production deployment stack. See `docs/SOURCES.md` for the relevant Python docs.

## How test execution works

1. The server receives your file through a same-origin local request.
2. It syntax-checks the file, then copies the relevant original pack to a temporary
   directory and replaces only the exercise file with your submission.
3. A separate process runs the selected original tests using the app’s interpreter.
4. A pytest reporting plugin records per-case outcomes and actual tracebacks.
5. The UI displays those records. Completion requires the expected test count,
   every selected case passing, and a successful process exit. Skips, empty
   collections, timeouts and syntax errors are not passes.
6. The temporary workspace is removed; your draft and result remain in progress.

This is a personal learning tool, not a cheating-resistant remote judge. Passing
finite tests is not proof of universal correctness. Some original V1 requirements
have less test coverage than their discussion follow-ups; the app calls that out.

## Troubleshooting

**Port already in use**

```bash
python run.py --port 8766
```

**Browser did not open:** use the local URL printed in the terminal.

**Missing dependency / wrong Python:** use the same interpreter for installation
and startup; check with:

```bash
python run.py --check
```

**A stale session-token error:** reload the browser after restarting the server.

**An infinite loop:** the runner stops the attempt after 20 seconds. Inspect the
feedback, fix the loop or task cleanup, and retry. A timer in the UI is independent.

**A concurrency timing assertion fails only on a very slow machine:** rerun and
inspect the implementation. Do not modify the original test just to get a badge.
Some V1 tests use wall-clock thresholds and can be sensitive to heavy machine load.

**Browser storage unavailable:** the app still uses its server-side progress file;
keep the server reachable and export regularly.

## Repository layout

```text
run.py                  Local entry point
requirements.txt        Versions used in validation
app/                    Local server, runner, feedback and activity catalog
web/                    UI, styles and bundled CodeMirror editor
packs/guided/           Original guided-search pack
packs/v2/               Original general-coding practice pack
packs/v1/               Original async/FastAPI practice pack
references/             NEW reference approaches; do not read before trying
tests_app/              Regression tests for the app itself
docs/                   Sources and validation notes
.judgelab/              Your progress (created on first use; not shipped)
```

`packs/` documents include instructions for running each pack independently;
use this top-level README for the UI setup.

## Development / verification

```bash
python -m pytest -q tests_app
```

These tests are for the app, not your exercise solutions. They cover real pytest
pass/fail, syntax errors, timeout handling, skipped-suite rejection, HTTP checks,
state persistence and transparent architecture feedback.

See `docs/VALIDATION.md` for exactly what was and was not tested for this delivery.
