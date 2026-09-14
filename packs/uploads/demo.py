"""After the upload/extraction checkpoints, run python demo.py. Synthetic data."""
from functools import partial
from tempfile import TemporaryDirectory
from pathlib import Path
from upload import upload_file
from extract import extract_lines
from storage import UploadSession
from indexing import open_index, index_revision


def main():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / 'source.txt'
        source.write_text('Lease renewal notice\nCafé meeting notes\n', encoding='utf-8')
        session = UploadSession(root / 'stored.txt', source.stat().st_size)
        with source.open('rb') as stream:
            print('Uploaded bytes:', upload_file(stream, session, part_size=7))
        db_path = str(root / 'tenant.sqlite')
        db = open_index(db_path)
        with session.path.open('rb') as stored:
            lines = extract_lines(iter(partial(stored.read, 5), b''), max_line_chars=100)
            index_revision(db, 'doc-1', 1, lines)
        db.close()
        db = open_index(db_path)
        print('Search after reopen:', db.execute(
            'SELECT document_id, section_id FROM sections WHERE sections MATCH ?', ('notice',)).fetchall())
        index_revision(db, 'doc-1', 2, iter(()))
        print('After deletion:', db.execute(
            'SELECT document_id FROM sections WHERE sections MATCH ?', ('notice',)).fetchall())
        db.close()


if __name__ == '__main__':
    main()
