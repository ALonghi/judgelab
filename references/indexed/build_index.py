"""Reference checkpoint 1: one unit's postings in memory at a time."""
import sqlite3
from collections.abc import Iterable
from models import SearchUnit
from text_tools import terms


def build_index(connection: sqlite3.Connection, units: Iterable[SearchUnit]) -> int:
    count = 0
    for unit in units:
        cursor = connection.execute(
            "INSERT INTO units(tenant_id, document_id, chunk_id, title, public) VALUES (?, ?, ?, ?, ?)",
            (unit.tenant_id, unit.document_id, unit.chunk_id, unit.title, int(unit.public)))
        unit_id = cursor.lastrowid
        connection.execute("INSERT INTO contents VALUES (?, ?)", (unit_id, unit.text))
        connection.executemany("INSERT INTO grants VALUES (?, ?)",
                               ((unit_id, user) for user in unit.allowed_users))
        title_terms, body_terms = terms(unit.title), terms(unit.text)
        connection.executemany("INSERT INTO postings VALUES (?, ?, ?, ?)",
            ((unit.tenant_id, term, unit_id,
              3 * (term in title_terms) + (term in body_terms))
             for term in title_terms | body_terms))
        count += 1
    return count
