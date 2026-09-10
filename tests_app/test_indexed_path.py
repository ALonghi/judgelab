"""Checks for the added curriculum and its actual runnable retrieval chain."""
import shutil
import subprocess
import sys

import pytest
from app.engine import ROOT, CATALOG, LESSONS, reference_text, run_code
from app.server import Store, lesson_payload


INDEXED_IDS = ('c-index-build', 'c-index-query', 'c-chunking')


def test_indexed_path_precedes_context_and_preserves_stable_ids():
    core = [lesson['id'] for lesson in CATALOG['lessons'] if lesson['track'] == 'core']
    sequence = ['c-search', *INDEXED_IDS, 'q-context', 'c-context']
    positions = [core.index(id) for id in sequence]
    assert positions == sorted(positions)
    assert LESSONS['q-context']['track'] == 'core'
    async_path = [l['id'] for l in CATALOG['lessons'] if l['track'] == 'async']
    assert async_path.index('a-fetch') < async_path.index('q-cancel') < async_path.index('a-federated')
    for lesson in CATALOG['lessons']:
        assert all(id in LESSONS for id in lesson.get('depends', []))


@pytest.mark.parametrize('id', INDEXED_IDS)
def test_indexed_references_pass_and_starters_fail_meaningfully(id):
    lesson = LESSONS[id]
    reference = run_code(lesson, reference_text(lesson))
    assert reference['success'], reference['output']
    assert reference['passed'] == lesson['expected_tests']
    starter = run_code(lesson, lesson['starter'])
    assert not starter['success']
    assert starter['failed'] > 0
    assert not starter['collection_errors'], starter['output']
    assert 'NotImplementedError' in starter['output']


def test_indexed_supporting_material_is_available_before_coding(tmp_path):
    payload = lesson_payload(LESSONS['c-index-query'], Store(tmp_path / 'progress.json'))
    names = {ref['name'] for ref in payload['references']}
    assert {'README.md', 'storage.py', 'models.py', 'text_tools.py', 'tests/test_query.py'} <= names
    assert 'search_index.py' not in names  # Complete reference remains gated.


def test_disk_index_to_ranked_chunks_to_existing_context(tmp_path):
    work = tmp_path / 'indexed'
    shutil.copytree(ROOT / 'packs/indexed', work)
    for name in ('build_index.py', 'search_index.py', 'chunk_documents.py'):
        shutil.copyfile(ROOT / 'references/indexed' / name, work / name)
    program = r'''
import runpy
import sys
from pathlib import Path
from models import Document
from storage import open_index, load_chunks
from build_index import build_index
from search_index import search_index
from chunk_documents import chunk_documents
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'packs/v2'))
build_context = runpy.run_path(str(root / 'references/v2/practice/round03_context.py'))['build_context']
db = open_index('integration.sqlite')
docs = iter([
    Document('a', 'd1', 'Manual', 'lease notice alpha beta', True),
    Document('a', 'd2', 'Notes', 'notice later', True),
    Document('a', 'secret', 'lease notice', 'lease notice', False, frozenset({'bob'})),
    Document('b', 'd1', 'lease notice', 'lease notice', True),
])
with db:
    assert build_index(db, chunk_documents(docs, max_words=2)) == 5
db.close()
db = open_index('integration.sqlite')
hits = search_index(db, 'lease notice', tenant_id='a', user_id='alice', limit=2)
assert [(h.document_id, h.chunk_id, h.score) for h in hits] == [('d1', '0', 2), ('d2', '0', 1)]
chunks = load_chunks(db, hits, tenant_id='a', user_id='alice')
context = build_context(chunks, tenant_id='a', user_id='alice', word_budget=4)
assert context.text == '[1] lease notice\n[2] notice later'.replace('\\n', '\n')
assert context.words_used == 4
assert [(c.document_id, c.chunk_id) for c in context.citations] == [('d1', '0'), ('d2', '0')]
db.execute("UPDATE units SET public=0 WHERE tenant_id='a' AND document_id='d2'")
assert [c.document_id for c in load_chunks(db, hits, tenant_id='a', user_id='alice')] == ['d1']
db.close()
print('Disk-backed index -> ranked chunks -> cited context passed')
'''
    result = subprocess.run([sys.executable, '-c', program, str(ROOT)], cwd=work,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    demo = subprocess.run([sys.executable, 'demo.py'], cwd=work,
                          capture_output=True, text=True, timeout=15)
    assert demo.returncode == 0, demo.stdout + demo.stderr
    assert 'Ready for context:' in demo.stdout
