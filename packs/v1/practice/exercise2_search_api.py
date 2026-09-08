from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from pydantic import BaseModel


@dataclass(frozen=True)
class StoredDocument:
    tenant_id: str
    document_id: str
    title: str
    text: str


class SearchResult(BaseModel):
    document_id: str
    title: str


class InMemoryRepository:
    def __init__(self, documents: list[StoredDocument]) -> None:
        self.documents = documents

    async def search(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int,
    ) -> list[StoredDocument]:
        """
        TODO: implement repository search.

        Keep tenant filtering here, not only in the HTTP handler.

        For this exercise, "search" is deliberately simple:
        - case-insensitive substring search in title OR text
        - preserve repository insertion order
        - return at most `limit` results
        """
        raise NotImplementedError


repository = InMemoryRepository(
    [
        StoredDocument("firm-a", "a-1", "Acme Contract", "Termination clause"),
        StoredDocument("firm-a", "a-2", "Employment Note", "Compensation analysis"),
        StoredDocument("firm-b", "b-1", "Acme Litigation", "Private strategy"),
    ]
)

app = FastAPI()


@app.get("/search", response_model=list[SearchResult])
async def search_documents():
    """
    Exercise 2: implement this FastAPI endpoint.

    API contract
    ------------
    GET /search?query=<text>&limit=<n>

    Required header:
        X-Tenant-ID

    Requirements
    ------------
    1. `query` is required and must contain at least 2 non-whitespace characters.
    2. `limit` defaults to 20 and must be between 1 and 100.
    3. `X-Tenant-ID` is required.
    4. Results must NEVER cross tenant boundaries.
    5. Map StoredDocument -> SearchResult.
    6. Use FastAPI validation where appropriate rather than hand-writing every
       possible 400 response.

    Interview follow-ups
    --------------------
    - Why should tenant isolation live below the route handler too?
    - Would you trust an application-layer filter alone in production?
    - What database index might help a real search implementation?
    - How would authn/authz differ from simply accepting X-Tenant-ID?
    - Where would tracing/metrics go?
    """
    raise NotImplementedError("Implement exercise 2")
