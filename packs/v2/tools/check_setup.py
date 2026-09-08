"""Check tooling only; exercise TODOs do not need to be solved."""
import importlib.metadata
import sys

if sys.version_info < (3, 13):
    raise SystemExit(f"Python >= 3.13 required, found {sys.version.split()[0]}")
try:
    version = importlib.metadata.version("pytest")
    import practice
except (ModuleNotFoundError, importlib.metadata.PackageNotFoundError):
    raise SystemExit("Run: python -m pip install -e . (inside your virtualenv)")
print(f"Python: {sys.version.split()[0]}")
print(f"pytest: {version}")
print(f"Package: {practice.__file__}")
print("Setup OK. Start with: python -m pytest -q tests/test_01_warmup.py -x")
