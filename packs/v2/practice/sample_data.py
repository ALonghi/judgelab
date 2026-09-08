"""Small synthetic corpus provided for experimentation; not client data."""
from practice.models import Document, Chunk

DOCUMENTS = [
    Document("firm-a", "d1", 1, "Termination clause", "Old notice wording",
             frozenset({"contract"}), frozenset({"alice"})),
    Document("firm-a", "d1", 2, "Termination clause", "Notice required for breach",
             frozenset({"contract", "employment"}), frozenset({"alice"})),
    Document("firm-a", "d2", 1, "Employment memo", "Termination notice discussion",
             frozenset({"memo"}), public=True),
    Document("firm-a", "d3", 1, "Termination termination", "Secret dispute advice",
             frozenset({"litigation"}), frozenset({"bob"})),
    Document("firm-b", "d1", 1, "Termination clause", "Different firm; confidential",
             frozenset({"contract"}), public=True),
]

CHUNKS = [
    Chunk("firm-a", "d1", "c1", "A notice period applies", frozenset({"alice"})),
    Chunk("firm-a", "d1", "c2", "Prior notice is required", frozenset({"alice"})),
    Chunk("firm-a", "d2", "c1", "Exceptions exist", public=True),
    Chunk("firm-a", "d3", "c1", "Never expose this", frozenset({"bob"})),
]
