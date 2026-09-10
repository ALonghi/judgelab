import pytest
from storage import open_index


@pytest.fixture
def db(tmp_path):
    connection = open_index(tmp_path / "search.sqlite")
    yield connection
    connection.close()


def seed(connection, key, weights, *, tenant="a", chunk="", public=True,
         allowed=(), title=None, text="body deliberately not used for scoring"):
    """Explicit fixture weights let query tests run without a solved builder."""
    cursor = connection.execute(
        "INSERT INTO units(tenant_id, document_id, chunk_id, title, public) VALUES (?, ?, ?, ?, ?)",
        (tenant, key, chunk, title or key, public))
    unit_id = cursor.lastrowid
    connection.execute("INSERT INTO contents VALUES (?, ?)", (unit_id, text))
    connection.executemany("INSERT INTO postings VALUES (?, ?, ?, ?)",
                          ((tenant, term, unit_id, weight) for term, weight in weights.items()))
    connection.executemany("INSERT INTO grants VALUES (?, ?)",
                          ((unit_id, user) for user in allowed))
    return unit_id
