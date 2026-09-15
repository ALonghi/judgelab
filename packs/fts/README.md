# Interview exercise: search a support portal with FTS5

Your team is adding search to a support portal. A customer types `reset password`
and expects articles about changing their password. A first version reads every
article in Python for every search. As the collection and traffic grow, that work
starts delaying responses. Use SQLite's built-in text search to find and rank
matches, while excluding articles the caller cannot read.

This is a 25-minute coding question with a design follow-up. Implement
`search_articles()` in `search.py`, then run:

```bash
python -m pytest -q tests/test_search.py
python demo.py
```

## What full-text search does for you

Full-text search means finding documents by the words in their text. SQLite FTS5
is an optional component of SQLite that provides this feature locally. You insert
article text; it records which articles contain each word and maintains that
lookup when you update or delete text. Your search reads the existing lookup.

The provided setup uses this SQL:

```sql
CREATE VIRTUAL TABLE articles USING fts5(
    document_id UNINDEXED, title, body, public UNINDEXED
);
```

`CREATE VIRTUAL TABLE ... USING fts5` asks SQLite to manage a searchable table.
`title` and `body` become searchable. `UNINDEXED` keeps IDs and the access flag
as stored values without treating them as search words. Each article also has a
SQLite `rowid`, used to associate user grants with that article. You do not create
or update a separate row for each word yourself.

## Follow one request

| ID | Title | Body | Visible to Sam? |
|---|---|---|---|
| reset | Reset account | Forgot your password? | Yes |
| router | Reset router | Restart your wireless device. | Yes |
| internal | Reset password | Internal recovery procedure. | No |

For `reset password`, both words must appear somewhere in the title or body.
`reset` matches even though the words are in different fields. `router` is missing
the word `password`. `internal` contains both words but is private. Return only
`reset`. This exercise uses complete words: `reset` does not match `resetting`.

The supplied `make_match_query()` helper turns `Reset, password!` into the FTS
expression `"reset" AND "password"`. It accepts English letters and digits, removes
duplicate words and treats punctuation as separators. An empty expression gives
no results. Do not build this helper yourself or accept arbitrary FTS syntax from
the search box in this exercise.

## Query the table

`MATCH` is SQLite's full-text query operator. A small example for one search word:

```python
rows = connection.execute(
    'SELECT document_id, title FROM articles WHERE articles MATCH ?',
    ('"router"',),
)
```

The `?` binds a SQL value safely. Quoting words *inside* the FTS expression is a
separate concern: it stops a word like `OR` becoming a query operator. The helper
does that part. For example, `reset OR password` searches for all three literal
words, including `or`.

FTS5 also calculates relevance. Its hidden `rank` column uses a formula called
BM25, which considers matching word frequency, how common words are in the stored
articles, and article length. You do not implement the formula. In SQLite FTS5,
lower numerical rank is better, so use `ORDER BY rank ASC`. Add
`document_id ASC` for equal ranks. These values are not the 3/1 points from the
earlier exercise and are not probabilities.

Before applying `LIMIT`, require either `public = 1` or a row in `grants` for
this `articles.rowid` and `user_id`. An `EXISTS` subquery checks for a grant without
duplicating the result when several users have access. Fetch only the limited
document IDs and titles into Python and return `FtsHit` records.

## What is supplied and what you implement

The caller has already authenticated the user and selected this customer's
database. `open_search()` creates the schema and `add_article()` writes fixture
articles and permissions. The provided `delete_article()` removes an article and
its grants together inside the caller's transaction. FTS5 maintains the text
index; it does not maintain the application’s permission rows. The only learner
task is the read query. Setup does
not call your previous manual index builder; the tests work independently.

Validate the integer limit in 1..100 before handling an empty query. Use the
provided query helper, `MATCH`, access filtering, default ascending `rank`, a
document-ID tie-break, and SQL `LIMIT`. Do not modify or close the connection.

The demo edits and deletes ordinary FTS5 rows, then repeats a query. FTS5 maintains
its text index with those writes; reopening the database reuses the stored index.
There is no external-content table or trigger setup to implement in this pack.

## Input size and table names

The supplied Article record contains a complete short support-article body.
This checkpoint starts with an existing database and teaches querying; its setup
is not a streaming large-file importer. SQL LIMIT bounds returned rows, while
matching and ranking can examine more rows inside SQLite.

`grants` means article access permissions: each row links `article_rowid` to one
allowed `user_id`. It belongs to this independent FTS schema. The manual chunk
index uses `document_access` because permissions apply to the shared document.

## Discuss the production decision

For a new portal, agree on expected document size, search traffic and the delay
allowed after an edit. For an existing portal, measure the slow searches. Database
text search is worth evaluating when repeated document scans are the bottleneck.
A separate search service becomes a candidate when required search features or
search load justify running and synchronizing another service.

Ask what users actually type. Do they expect every word to match, an exact phrase
such as `"reset password"`, or either word? This exercise chooses every word;
FTS5 can express the other cases, but they change which articles match. Test a
small set of real questions and expected useful articles before tuning ranking.

This pack uses one SQLite file per customer to keep the learning task focused.
That deployment choice has backup, connection and migration costs at scale. A
shared database needs explicit customer isolation. Access filtering here removes
private results, but default relevance statistics still include all articles in
this customer's database. Stricter isolation of ranking signals needs a separate
design. FTS5 is not automatic typo correction or semantic search.

SQLite must be built with FTS5 support. If setup reports `no such module: fts5`,
use a Python/SQLite build that includes it; this is a missing runtime capability,
not a failing learner solution.

Sources: [SQLite FTS5 overview and queries](https://www.sqlite.org/fts5.html),
[FTS5 ranking](https://www.sqlite.org/fts5.html#the_bm25_function).
