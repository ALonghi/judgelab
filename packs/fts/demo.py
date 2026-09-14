"""Run after implementing search.py. Uses synthetic data in a temporary file."""
from pathlib import Path
from tempfile import TemporaryDirectory

from models import Article
from search import search_articles
from storage import open_search, add_article, delete_article


def main():
    with TemporaryDirectory(prefix='judgelab-fts-') as directory:
        path = Path(directory) / 'customer.sqlite'
        db = open_search(path)
        with db:
            reset_rowid = add_article(db, Article('reset', 'Reset password', 'Open account settings.', True))
            add_article(db, Article('wifi', 'Reset router', 'Restart the wireless device.', True))
            add_article(db, Article('private', 'Reset password', 'Internal recovery procedure.'))
        print('Search:', search_articles(db, 'reset password', user_id='sam'))
        with db:
            db.execute("UPDATE articles SET title = ? WHERE document_id = ?",
                       ('Change password', 'reset'))
        print('After edit:', search_articles(db, 'reset password', user_id='sam'))
        db.close()
        db = open_search(path)
        print('After reopen:', search_articles(db, 'change password', user_id='sam'))
        with db:
            delete_article(db, reset_rowid)
        print('After delete:', search_articles(db, 'change password', user_id='sam'))
        db.close()


if __name__ == '__main__':
    main()
