import pytest
from storage import open_index


@pytest.fixture
def db(tmp_path):
    connection = open_index(tmp_path / "search.sqlite")
    yield connection
    connection.close()


def seed(connection, key, weights, *, tenant="a", chunk="0", public=True,
         allowed=(), title=None, text="body deliberately not used for scoring"):
    """Explicit fixture weights let query tests run without a solved builder."""
    connection.execute("INSERT INTO documents VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING",
                       (tenant, key, title or key, public))
    connection.executemany("INSERT INTO document_access VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                          ((tenant, key, user) for user in allowed))
    cursor = connection.execute(
        "INSERT INTO chunks(tenant_id, document_id, chunk_id) VALUES (?, ?, ?)",
        (tenant, key, chunk))
    chunk_pk = cursor.lastrowid
    connection.execute("INSERT INTO chunk_texts VALUES (?, ?)", (chunk_pk, text))
    connection.executemany("INSERT INTO term_chunks VALUES (?, ?, ?, ?)",
                          ((tenant, term, chunk_pk, weight) for term, weight in weights.items()))
    return chunk_pk
