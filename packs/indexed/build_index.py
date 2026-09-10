"""Checkpoint 1. Read README.md. Edit this file; schema/helpers are provided."""
import sqlite3
from collections.abc import Iterable
from models import SearchUnit
from text_tools import terms


def build_index(connection: sqlite3.Connection, units: Iterable[SearchUnit]) -> int:
    """Append unique units to an initialized index and return their count.

    For each unit, write units metadata, contents text, grants, and postings.
    One posting per distinct term in title OR body: weight = 3 for title,
    independently +1 for body. Repetition never adds weight. Use terms().
    Posting identity is (tenant_id, term, unit_id); unit_id is units.id.
    Store units even if their title/body have no tokens. Keep empty chunk_id
    for whole documents. IDs are unique in input and absent from the database.
    Process/write each unit BEFORE requesting the next. Do not list() input,
    retain all documents/postings, or mutate input. Keep one unit's term sets.
    Do not commit/rollback/close: the caller owns the transaction/connection.
    Invalid duplicate identities may raise sqlite3.IntegrityError; updates,
    deletion and version conflict handling are outside this checkpoint.
    """
    raise NotImplementedError("Build the disk-backed inverted index")
