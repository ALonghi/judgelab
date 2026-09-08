"""Provided data types. These are scaffolding, not functions you need to implement.

All examples are synthetic. Permissions in this pack are intentionally simplified:
a document is readable iff the tenant matches and it is public WITHIN that tenant
or the user appears in allowed_users. Public never means cross-tenant public.
User and tenant identities are assumed to have already been authenticated.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    tenant_id: str
    document_id: str
    version: int
    title: str
    text: str
    categories: frozenset[str] = frozenset()
    allowed_users: frozenset[str] = frozenset()
    public: bool = False


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    title: str
    score: int

