"""Regression checks for JudgeLab itself (separate from the learner's tests)."""
import json
import threading
import urllib.request
import urllib.error
from pathlib import Path

import pytest
from app.engine import (ROOT, LESSONS, CATALOG, run_code, reference_text,
                        interview_feedback, fingerprint)
from app.server import Store, LabHTTPServer, Handler, public_catalog


def test_catalog_has_expected_modes_and_unique_ids():
    assert len(LESSONS)==41
    assert len({x['id'] for x in CATALOG['lessons']})==41
    assert sum(x['kind']=='code' for x in LESSONS.values())==16
    assert sum(x['kind']=='quiz' for x in LESSONS.values())==8
    assert sum(x['kind']=='interview' for x in LESSONS.values())==17


def test_all_code_assets_exist_and_have_test_counts():
    for lesson in LESSONS.values():
        if lesson['kind']!='code':continue
        assert (ROOT/'packs'/lesson['pack']/lesson['file']).exists()
        assert (ROOT/'references'/lesson['pack']/lesson['file']).exists()
        assert lesson['expected_tests']>0
        for test in lesson['tests']:assert (ROOT/'packs'/lesson['pack']/test).exists()


def test_quiz_keys_are_not_in_bootstrap():
    for lesson in public_catalog()['lessons']:
        assert 'correct' not in lesson
        assert 'guide' not in lesson


def test_guided_reference_does_not_reveal_next_stage():
    text=reference_text(LESSONS['g-score'])
    assert 'def score_document' in text
    assert 'def can_read' not in text


def test_syntax_error_is_not_a_test_pass():
    result=run_code(LESSONS['g-score'],'def broken(:\n  pass')
    assert not result['success']
    assert result['collected']==0
    assert 'SyntaxError' in result['collection_errors'][0]


def test_starter_returns_real_failures():
    lesson=LESSONS['g-score']
    result=run_code(lesson,lesson['starter'])
    assert not result['success']
    assert result['failed']==9
    assert 'NotImplementedError' in result['records'][0]['detail']


def test_reference_passes_actual_pytest_and_records_exact_submission():
    lesson=LESSONS['g-score']
    code=(ROOT/'references/guided/exercise.py').read_text()
    result=run_code(lesson,code)
    assert result['success']
    assert result['passed']==result['collected']==9
    assert result['submitted_text']==code
    assert result['code_hash']==fingerprint(code)


def test_skipping_the_module_does_not_award_a_pass():
    result=run_code(LESSONS['g-score'],"import pytest\npytest.skip('not an answer', allow_module_level=True)\n")
    assert not result['success']
    assert result['collected']==0


def test_timeout_is_not_a_pass():
    result=run_code(LESSONS['g-score'],'while True:\n    pass\n',timeout_s=2.5)
    assert result['timed_out']
    assert not result['success']
    assert result['elapsed']<8


def test_interview_cues_are_not_a_semantic_score():
    result=interview_feedback(LESSONS['i-performance'], 'I measured the database. The performance improved after the change. ' * 4)
    assert result['can_review']
    assert 'score' not in result
    assert result['submitted_text']
    assert 'not semantic grading' in result['note']
    assert not interview_feedback(LESSONS['i-performance'],'Nice job')['can_review']


def test_progress_persists_and_xp_is_not_farmed(tmp_path):
    store=Store(tmp_path/'progress.json')
    lesson=LESSONS['q-score']
    with store.lock:
        store.record(lesson,True,'quiz');store.record(lesson,True,'quiz');store.persist()
    loaded=Store(store.path)
    assert loaded.state['attempts']['q-score']==2
    assert len(loaded.state['completed'])==1
    assert loaded.state['completed']['q-score']['xp']==lesson['xp']


@pytest.fixture(scope='module')
def http_app(tmp_path_factory):
    server=LabHTTPServer(('127.0.0.1',0),Handler)
    server.store=Store(tmp_path_factory.mktemp('http-state')/'progress.json')
    server.token='test-token'
    server.run_lock=threading.Lock()
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}', server
    server.shutdown();server.server_close();thread.join(timeout=3)


def request(base,path,body=None,headers=None):
    request_headers=headers or {}
    if body is not None:
        request_headers={'Content-Type':'application/json',**request_headers}
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=request_headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status,response.read(),dict(response.headers)
    except urllib.error.HTTPError as error:return error.code,error.read(),dict(error.headers)


def test_http_bootstrap_and_static_assets(http_app):
    base,_=http_app
    status,body,headers=request(base,'/api/bootstrap')
    assert status==200
    assert json.loads(body)['token']=='test-token'
    assert headers['X-Frame-Options']=='DENY'
    for path in ['/','/app.js','/app.css','/vendor/codemirror.js']:
        assert request(base,path)[0]==200


def test_host_and_origin_checks(http_app):
    base,_=http_app
    assert request(base,'/api/bootstrap',headers={'Host':'attacker.example'})[0]==403
    assert request(base,'/api/save',{'id':'g-score','text':''},{'X-Lab-Token':'test-token','Origin':'https://attacker.example'})[0]==403
    assert request(base,'/api/save',{'id':'g-score','text':''})[0]==403


def test_no_arbitrary_static_file_access(http_app):
    base,_=http_app
    for path in ['/%2e%2e/app/catalog.json','/references/guided/exercise.py','/.judgelab/progress.json']:
        assert request(base,path)[0]==404


def test_run_requires_explicit_local_execution_consent(http_app):
    base,_=http_app
    status,body,_=request(base,'/api/run',{'id':'g-score','text':'pass'},{'X-Lab-Token':'test-token'})
    assert status==400
    assert 'warning' in json.loads(body)['error']


def test_quiz_correction_and_reference_attempt_gate(http_app):
    base,_=http_app
    headers={'X-Lab-Token':'test-token'}
    assert request(base,'/api/reveal',{'id':'g-score'},headers)[0]==400
    status,body,_=request(base,'/api/quiz',{'id':'q-score','choice':0},headers)
    data=json.loads(body)
    assert status==200 and not data['result']['success']
    assert data['result']['correct']==2
    assert '5' in data['result']['explanation']


def test_save_and_export_are_real_server_state(http_app):
    base,_=http_app
    headers={'X-Lab-Token':'test-token'}
    assert request(base,'/api/save',{'id':'g-score','text':'# my draft'},headers)[0]==200
    status,body,_=request(base,'/api/export')
    assert json.loads(body)['drafts']['guided/exercise.py']['text']=='# my draft'
