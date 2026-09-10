"""Same deliberately small whole-token policy as the guided search pack."""
import re


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))
