"""Provided toy tokenizer; not representative of production legal search.

The exercises deliberately use ASCII letters/digits and whole-token matching.
For example, "Non-compete, NDA!" -> {"non", "compete", "nda"}.
Repeated words do not change the output. Real multilingual tokenization is a
follow-up discussion, not a requirement here.
"""
import re


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))
