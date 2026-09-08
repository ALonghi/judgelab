# Validation notes

Environment used: **CPython 3.13.5**, **pytest 9.0.2**.

## Starter pack

- All Python files compile and all 91 test cases collect without import errors.
- `tests/test_setup.py`: **3 passed**.
- Entire intentionally incomplete starter suite: **3 passed, 88 failed**.
- Failures come from exercise TODOs. No completed exercise implementation is shipped.

## Acceptance-test check

A separate private reference implementation was used to check that the exercise
contracts are satisfiable and the assertions agree with the prompts:

- Full reference suite: **91 passed**.
- The 12 async cases were also rerun three additional times successfully.
- Tests also passed with third-party pytest plugin auto-loading disabled; this pack
  does not require pytest-asyncio or FastAPI.
- The search, context, and stream demos were exercised against that reference.

The reference implementation is **not included** in the archive. These tests cover
the stated exercise contracts, not every possible production failure or security case.

## Packaging and installation

An editable package install was checked using existing local dependencies with
`--no-index --no-build-isolation --no-deps`. The setup checker and setup tests passed
through that installed package.

A fully isolated `pip install -e .` with fresh dependency downloads was attempted
but could not be completed: this environment could not resolve the package-index
host. The normal setup commands therefore assume that your machine can download
pytest and the setuptools build backend. Windows commands are provided but were
not executed on a Windows host.

## Archive hygiene

The download includes source files, tests, prompts, and documentation only. It does
not contain solutions, virtual environments, bytecode, pytest caches, credentials,
client documents, or third-party package distributions. The earlier practice archive
has not been overwritten.
