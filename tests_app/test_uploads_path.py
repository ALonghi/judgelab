import subprocess
import sys
import pytest
from app.engine import ROOT, CATALOG, LESSONS, reference_text, run_code
from app.server import Store, lesson_payload, public_catalog


IDS = ('u-upload', 'u-batch', 'u-extract')


def test_api_precedes_search_and_saved_ids_survive():
    tracks = [t['id'] for t in CATALOG['tracks']]
    assert tracks.index('api') < tracks.index('guided') < tracks.index('core')
    ids = [l['id'] for l in CATALOG['lessons']]
    assert ids.index('p-fastapi') < ids.index('g-score') < ids.index('c-index-build')
    assert LESSONS['p-fastapi']['workspace'] == 'v1/practice/exercise2_search_api.py'
    assert ids.index('p-ingest') < ids.index('q-version') < ids.index('c-events')
    assert ids.index('a-fetch') < ids.index('u-upload') < ids.index('u-batch') < ids.index('u-extract')


@pytest.mark.parametrize('id', IDS)
def test_reference_passes_starter_fails_assertions(id):
    lesson = LESSONS[id]
    result = run_code(lesson, reference_text(lesson))
    assert result['success'], result['output']
    assert result['passed'] == lesson['expected_tests']
    starter = run_code(lesson, lesson['starter'])
    assert starter['failed'] and not starter['success'], starter['output']
    assert not starter['collection_errors'], starter['output']
    assert 'NotImplementedError' in starter['output']


def test_support_visible_and_references_remain_gated(tmp_path):
    for id in IDS:
        lesson = LESSONS[id]
        payload = lesson_payload(lesson, Store(tmp_path / 'progress.json'))
        names = {r['name'] for r in payload['references']}
        assert {'README.md', 'models.py', 'storage.py', 'indexing.py', 'demo.py'} <= names
        assert lesson['file'] not in names
        assert lesson['starter'] == (ROOT / 'packs/uploads' / lesson['file']).read_text()
    public = next(l for l in public_catalog()['lessons'] if l['id'] == 's-large-import')
    assert 'guide' not in public
    assert public['flow_ref'] == 'large-import'


def test_uploaded_bytes_become_searchable_and_delete_with_supplied_bridge():
    program = '''
import sys, types, runpy
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'packs/uploads'))
for name in ('upload', 'extract'):
    module = types.ModuleType(name)
    exec((root / 'references/uploads' / (name + '.py')).read_text(), module.__dict__)
    sys.modules[name] = module
runpy.run_path(str(root / 'packs/uploads/demo.py'), run_name='__main__')
'''
    result = subprocess.run([sys.executable, '-c', program, str(ROOT)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Search after reopen: [('doc-1', 0)]" in result.stdout
    assert 'After deletion: []' in result.stdout


@pytest.mark.parametrize('variant', ['smaller_reads', 'copied_parts', 'assembled_parts'])
def test_upload_accepts_contract_compliant_buffer_choices(variant):
    lesson = LESSONS['u-upload']
    code = reference_text(lesson)
    if variant == 'smaller_reads':
        code = code.replace('min(part_size, session.total_size - offset)',
                            'min(part_size, 64 * 1024, session.total_size - offset)')
    elif variant == 'copied_parts':
        code = code.replace('        if not data:',
                            '        data = bytes(bytearray(data))\n        if not data:')
    elif variant == 'assembled_parts':
        code = code.replace(
            '        data = source.read(min(part_size, session.total_size - offset))',
            '''        read_size = min(part_size, session.total_size - offset)
        data = bytearray()
        while len(data) < read_size:
            fragment = source.read(min(64 * 1024, read_size - len(data)))
            if not fragment:
                raise EOFError('Source ended while assembling a part')
            data.extend(fragment)
        data = bytes(data)''')
    result = run_code(lesson, code)
    assert result['success'], result['output']
