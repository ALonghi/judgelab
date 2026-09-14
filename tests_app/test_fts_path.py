import subprocess
import sys

from app.engine import ROOT, LESSONS, CATALOG, reference_text, run_code
from app.server import Store, lesson_payload, public_catalog


def test_fts_follows_manual_index_query_and_has_independent_workspace():
    ids = [lesson['id'] for lesson in CATALOG['lessons'] if lesson['track'] == 'core']
    assert ids.index('c-index-query') < ids.index('c-fts') < ids.index('c-chunking')
    assert LESSONS['c-fts']['workspace'] == 'fts/search.py'
    assert not LESSONS['c-fts'].get('optional')


def test_fts_reference_passes_and_starter_fails_real_tests():
    lesson = LESSONS['c-fts']
    result = run_code(lesson, reference_text(lesson))
    assert result['success'], result['output']
    assert result['passed'] == 15
    starter = run_code(lesson, lesson['starter'])
    assert not starter['success']
    assert starter['failed'] > 0
    assert not starter['collection_errors'], starter['output']
    assert 'NotImplementedError' in starter['output']


def test_fts_support_is_visible_without_exposing_reference(tmp_path):
    lesson = LESSONS['c-fts']
    payload = lesson_payload(lesson, Store(tmp_path / 'progress.json'))
    names = {ref['name'] for ref in payload['references']}
    assert {'README.md', 'models.py', 'storage.py', 'demo.py', 'tests/test_search.py'} <= names
    assert 'search.py' not in names
    public = next(item for item in public_catalog()['lessons'] if item['id'] == 'c-fts')
    assert public['starter'] == (ROOT / 'packs/fts/search.py').read_text()
    assert 'explanation' not in public


def test_fts_demo_runs_with_completed_reference():
    # Provide the reference only to this subprocess; the learner file stays TODO.
    program = '''
import runpy, sys, types
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "packs/fts"))
module = types.ModuleType("search")
exec((root / "references/fts/search.py").read_text(), module.__dict__)
sys.modules["search"] = module
runpy.run_path(str(root / "packs/fts/demo.py"), run_name="__main__")
'''
    result = subprocess.run([sys.executable, '-c', program, str(ROOT)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "document_id='reset'" in result.stdout
    assert 'After edit: []' in result.stdout
    assert 'After delete: []' in result.stdout
