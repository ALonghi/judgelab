"""Synthetic support articles for one customer's local search database."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    document_id: str
    title: str
    body: str
    public: bool = False
    allowed_users: frozenset[str] = frozenset()


@dataclass(frozen=True)
class FtsHit:
    document_id: str
    title: str
