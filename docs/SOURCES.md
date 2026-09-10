# Project content and references

## Practice packs

- `packs/guided/`: staged search exercise with helper functions.
- `packs/v2/`: progressive Python exercises for search, context and ingestion.
- `packs/v1/`: additional FastAPI and async exercises.

The source-test SHA-256 manifest records the current bundled tests. Exercise data
is synthetic. Scoring weights, visibility rules and event protocols are simplified
teaching contracts.

## Application additions

The UI adds XP, eight concept checks, hints, coaching text, reference solutions and
self-review rubrics. Architecture discussion prompts extend the coding exercises with system-design
questions.

Reference implementations are checked against the selected exercise tests. Passing
these tests does not establish every production property. Word and substring cues
help structure discussion answers; they do not evaluate meaning or verify facts.

## Primary technical documentation consulted

- Python 3.13 subprocess: https://docs.python.org/3.13/library/subprocess.html
- Python HTTP server and its production warning: https://docs.python.org/3.13/library/http.server.html
- pytest reporting hooks and API: https://docs.pytest.org/en/stable/reference/reference.html

## Bundled editor

CodeMirror 5.58.3 is bundled from the locally available nbclassic installation to
avoid a CDN dependency. Its source headers credit Marijn Haverbeke and others and
specify the MIT license. The notice is retained in `web/vendor/CodeMirror-LICENSE.txt`.
This app uses the editor for local practice, not as a newly maintained upstream fork.
There are no bundled fonts or external frontend requests.
