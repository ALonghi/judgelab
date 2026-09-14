"""Provided FTS5 setup and query preparation. Learners edit search.py only."""
import re
import sqlite3
from pathlib import Path

from models import Article


def open_search(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    # This database belongs to one customer. Authentication and database
    # selection are the caller's responsibility and are outside the exercise.
    connection.executescript('''
        CREATE VIRTUAL TABLE IF NOT EXISTS articles USING fts5(
            document_id UNINDEXED, title, body, public UNINDEXED
        );
        CREATE TABLE IF NOT EXISTS grants (
            article_rowid INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            PRIMARY KEY (article_rowid, user_id)
        );
    ''')
    return connection


def add_article(connection: sqlite3.Connection, article: Article) -> int:
    """Fixture adapter: write text once and let FTS5 maintain its own word index."""
    rowid = connection.execute(
        'INSERT INTO articles(document_id, title, body, public) VALUES (?, ?, ?, ?)',
        (article.document_id, article.title, article.body, int(article.public)),
    ).lastrowid
    connection.executemany('INSERT INTO grants VALUES (?, ?)',
                           ((rowid, user) for user in article.allowed_users))
    return rowid


def make_match_query(query: str) -> str | None:
    """All distinct English letter/digit words must match; punctuation separates words.

    Quote words so user input cannot become FTS operators. SQL values must still
    be bound separately with ? placeholders by the caller.
    """
    words = dict.fromkeys(re.findall(r'[a-z0-9]+', query.lower()))
    return ' AND '.join(f'"{word}"' for word in words) if words else None


def delete_article(connection: sqlite3.Connection, rowid: int) -> None:
    """Remove permissions with the article; the caller owns the transaction.

    FTS5 maintains the text index, but it does not maintain our grants table.
    Removing grants also prevents a reused SQLite rowid inheriting old access.
    """
    connection.execute('DELETE FROM grants WHERE article_rowid = ?', (rowid,))
    connection.execute('DELETE FROM articles WHERE rowid = ?', (rowid,))
