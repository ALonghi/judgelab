"""Optional scratchpad: python sandbox.py. Edit freely; tests do not import it."""
from text_tools import terms

# These work immediately; no exercise implementation is required.
print("Query terms:", terms("Termination, NOTICE! notice"))
print("Whole-token membership:", "notice" in terms("notices"))
print("Shared categories:", frozenset({"memo", "contract"}) & frozenset({"memo"}))

# After Stage 1, try constructing a Document and calling score_document here.
