from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Header, Query, HTTPException
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
        query = query.casefold()
        return [doc for doc in self.documents
                if doc.tenant_id == tenant_id
                and (query in doc.title.casefold() or query in doc.text.casefold())][:limit]


repository = InMemoryRepository(
    [
        StoredDocument("firm-a", "a-1", "Acme Contract", "Termination clause"),
        StoredDocument("firm-a", "a-2", "Employment Note", "Compensation analysis"),
        StoredDocument("firm-b", "b-1", "Acme Litigation", "Private strategy"),
    ]
)

app = FastAPI()


@app.get("/search", response_model=list[SearchResult])
async def search_documents(
    query: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    x_tenant_id: str = Header(...),
) -> list[SearchResult]:
    query = query.strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="Query must contain at least two non-whitespace characters")
    documents = await repository.search(tenant_id=x_tenant_id, query=query, limit=limit)
    return [SearchResult(document_id=doc.document_id, title=doc.title) for doc in documents]
