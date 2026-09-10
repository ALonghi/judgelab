"""Regression checks for JudgeLab itself (separate from the learner's tests)."""
import json
import threading
import urllib.request
import urllib.error
from pathlib import Path

import pytest
from app.engine import (ROOT, LESSONS, CATALOG, run_code, reference_text,
                        discussion_feedback, fingerprint)
from app.server import Store, LabHTTPServer, Handler, public_catalog


def test_catalog_has_expected_modes_and_unique_ids():
    assert len(LESSONS)==32
    assert len({x['id'] for x in CATALOG['lessons']})==32
    assert sum(x['kind']=='code' for x in LESSONS.values())==19
    assert sum(x['kind']=='quiz' for x in LESSONS.values())==8
    assert sum(x['kind']=='discussion' for x in LESSONS.values())==5


def test_all_code_assets_exist_and_have_test_counts():
    for lesson in LESSONS.values():
        if lesson['kind']!='code':continue
        assert (ROOT/'packs'/lesson['pack']/lesson['file']).exists()
        assert (ROOT/'references'/lesson['pack']/lesson['file']).exists()
        assert lesson['expected_tests']>0
        for test in lesson['tests']:assert (ROOT/'packs'/lesson['pack']/test).exists()


def test_every_activity_exposes_context_before_an_attempt():
    for lesson in public_catalog()['lessons']:
        assert lesson['scenario']['prompt'] and lesson['scenario']['deliverable']
        assert len(lesson['scenario']['requirements']) >= 2
        brief = lesson['brief']
        for field in ('heading', 'scenario', 'rule', 'example'):
            assert brief[field].strip(), (lesson['id'], field)
        assert brief['vocabulary'], lesson['id']
        assert all(item['term'] and item['meaning'] for item in brief['vocabulary'])
        strategy = lesson['strategy']
        for field in ('name', 'mechanism', 'use_case', 'prompt', 'recognize', 'proposal'):
            assert strategy[field].strip(), (lesson['id'], field)
        assert len(strategy['caveats']) >= 2, lesson['id']
        assert all(strategy['caveats'])
        for reference in strategy['references']:
            assert reference['title'] and reference['url'].startswith('https://')
        assert 'correct' not in lesson
        assert 'explanation' not in lesson
        problem = lesson['problem']
        assert problem['title'] and problem['problem']
        assert len(problem['reasoning']) >= 2
        assert all(problem['reasoning'])
        implementation = lesson['implementation']
        assert implementation['state'] and implementation['result']
        assert len(implementation['steps']) >= 3
        assert implementation['decisions']
        for decision in implementation['decisions']:
            assert decision['question']
            assert decision['lead_in'].strip(), lesson['id']
            assert len(decision['branches']) >= 2
            assert all(branch['answer'] and branch['action'] for branch in decision['branches'])
        for link in implementation.get('connections', []):
            assert link['id'] in LESSONS and link['text']


def test_budget_teaching_examples_match_their_trace():
    guide = LESSONS['q-context']['implementation']
    ranking = {}
    exec(guide['ranking_code'], ranking)
    assert ranking['ranked'] == [('A', 2), ('B', 1), ('C', 1)]
    selection = {}
    exec(guide['code'], selection)
    assert selection['selected'] == ['A', 'C']
    assert selection['remaining'] == 30
    remaining = 800
    for (chunk_id, cost), row in zip(selection['chunks'], guide['trace']['rows'], strict=True):
        assert row[:3] == [chunk_id, str(cost), str(remaining)]
        fits = cost <= remaining
        if fits:
            remaining -= cost
        assert row[3].startswith('Keep' if fits else 'Skip')
        assert int(row[4]) == remaining


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


def test_discussion_cues_are_not_a_semantic_score():
    result=discussion_feedback(LESSONS['s-search'], 'I measured the database. The performance improved after the change. ' * 4)
    assert result['can_review']
    assert 'score' not in result
    assert result['submitted_text']
    assert 'not semantic grading' in result['note']
    assert not discussion_feedback(LESSONS['s-search'],'Nice job')['can_review']


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


def test_studio_removed_but_architecture_review_still_works(http_app):
    base, _ = http_app
    headers = {'X-Lab-Token': 'test-token'}
    assert {t['id'] for t in CATALOG['tracks']} == {
        'basics', 'guided', 'core', 'async', 'api', 'architecture'}
    assert not any(l['id'].startswith('i-') for l in LESSONS.values())
    assert request(base, '/api/lesson/i-intro')[0] == 404
    answer = 'Measure query latency and volume, index eligible documents, and enforce tenant permissions before ranking. Track cache invalidation after access changes and benchmark the trade-offs under representative load.'
    status, body, _ = request(base, '/api/discussion',
                              {'id': 's-search', 'text': answer}, headers)
    assert status == 200
    assert json.loads(body)['result']['can_review']
    status, _, _ = request(base, '/api/review',
                           {'id': 's-search', 'checks': ['yes'] * 4}, headers)
    assert status == 200
