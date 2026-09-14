import pytest

from models import Article, FtsHit
from search import search_articles
from storage import open_search, add_article, delete_article


@pytest.fixture
def db(tmp_path):
    connection = open_search(tmp_path / 'customer.sqlite')
    yield connection
    connection.close()


def put(db, key, title, body='', public=True, allowed=()):
    return add_article(db, Article(key, title, body, public, frozenset(allowed)))


def search(db, query='reset password', **kwargs):
    return search_articles(db, query, user_id='sam', **kwargs)


def test_all_query_words_can_match_across_title_and_body(db):
    put(db, 'both', 'Reset account', 'Forgot your password?')
    put(db, 'one', 'Reset router')
    assert search(db) == [FtsHit('both', 'Reset account')]


def test_complete_words_case_and_repetition(db):
    put(db, 'yes', 'RESET password')
    put(db, 'no', 'Resetting passwords')
    assert search(db, 'Reset, PASSWORD password!') == [FtsHit('yes', 'RESET password')]


def test_readable_results_fill_limit_and_grants_do_not_duplicate_hits(db):
    put(db, 'secret', 'reset password', public=False)
    put(db, 'shared', 'Reset', 'Password instructions', False, ('sam', 'jo'))
    put(db, 'public', 'Reset', 'Password instructions')
    assert [h.document_id for h in search(db, limit=2)] == ['public', 'shared']


def test_default_rank_orders_better_match_first(db):
    put(db, 'z-short', 'Reset password')
    put(db, 'a-long', 'Reset password', 'Extra unrelated background information ' * 30)
    assert [h.document_id for h in search(db)] == ['z-short', 'a-long']


def test_equal_rank_uses_document_id_not_insertion_order(db):
    for key in ['z', 'a', 'm']:
        put(db, key, 'Reset password')
    assert [h.document_id for h in search(db, limit=2)] == ['a', 'm']


@pytest.mark.parametrize('query', ['', '!?', 'missing'])
def test_empty_and_unmatched_queries(db, query):
    put(db, 'a', 'Reset password')
    assert search(db, query) == []


@pytest.mark.parametrize('limit', [0, -1, 101])
def test_invalid_limit_rejected_before_empty_query(db, limit):
    with pytest.raises(ValueError):
        search(db, '', limit=limit)


def test_user_values_are_bound_and_query_operators_are_literal_words(db):
    put(db, 'own', 'Reset OR password', public=False, allowed=("sam'",))
    put(db, 'secret', 'Reset OR password', public=False, allowed=('jo',))
    put(db, 'single', 'Reset')
    assert search_articles(db, 'reset OR password', user_id="sam'") == [FtsHit('own', 'Reset OR password')]


def test_fts5_tracks_edits_deletes_and_reopen(tmp_path):
    path = tmp_path / 'persist.sqlite'
    db = open_search(path)
    with db:
        rowid = put(db, 'd', 'Reset password')
    assert search(db)
    with db:
        db.execute('UPDATE articles SET title = ? WHERE rowid = ?', ('Change password', rowid))
    assert search(db) == []
    db.close()
    db = open_search(path)
    try:
        assert search(db, 'change password') == [FtsHit('d', 'Change password')]
        with db:
            delete_article(db, rowid)
        assert search(db, 'change password') == []
    finally:
        db.close()


def test_permission_change_affects_next_search(db):
    rowid = put(db, 'd', 'Reset password', public=False, allowed=('sam',))
    assert search(db)
    db.execute('DELETE FROM grants WHERE article_rowid = ?', (rowid,))
    assert search(db) == []
    db.execute('INSERT INTO grants VALUES (?, ?)', (rowid, 'sam'))
    delete_article(db, rowid)
    put(db, 'replacement', 'Reset password', public=False)
    assert search(db) == []  # A reused SQLite rowid must not inherit old grants.


def test_search_uses_match_and_limits_rows_before_python(db):
    for i in range(50):
        put(db, f'{i:02}', 'Reset password')
    queries = []
    db.set_trace_callback(queries.append)

    class LimitedRows:
        def execute(self, sql, values=()):
            cursor = db.execute(sql, values)

            class Cursor:
                def __iter__(self):
                    return self

                def __next__(self):
                    row = self.fetchone()
                    if row is None:
                        raise StopIteration
                    return row

                def fetchone(self):
                    row = cursor.fetchone()
                    if row is not None:
                        self_read[0] += 1
                        assert self_read[0] <= 2, 'Apply LIMIT before fetching matches into Python'
                    return row

                def fetchall(self):
                    return list(self)

                def fetchmany(self, size=1):
                    rows = []
                    for _ in range(size):
                        row = self.fetchone()
                        if row is None:
                            break
                        rows.append(row)
                    return rows

            return Cursor()

    self_read = [0]
    before = db.total_changes
    assert len(search(LimitedRows(), limit=2)) == 2
    assert self_read[0] == 2
    assert db.total_changes == before
    assert db.in_transaction
    assert any('MATCH' in sql.upper() for sql in queries if sql.lstrip().upper().startswith('SELECT'))
    db.rollback()  # Search must not commit caller-owned writes.
    assert db.execute('SELECT count(*) FROM articles').fetchone() == (0,)
