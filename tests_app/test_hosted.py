import http.client
from urllib.parse import urlsplit, urlencode
import time
import hmac
import json
import threading

import pytest

from app.server import Handler, LabHTTPServer, Store, hosted_settings
from test_app import request


@pytest.mark.parametrize('environment', [
    {}, {'JUDGELAB_PUBLIC_ORIGIN': 'https://lab.example'},
    {'JUDGELAB_PUBLIC_ORIGIN': 'http://lab.example', 'JUDGELAB_PASSWORD': 'x'*32},
    {'JUDGELAB_PUBLIC_ORIGIN': 'https://user@lab.example', 'JUDGELAB_PASSWORD': 'x'*32},
    {'JUDGELAB_PUBLIC_ORIGIN': 'https://lab.example/path', 'JUDGELAB_PASSWORD': 'x'*32},
    {'JUDGELAB_PUBLIC_ORIGIN': 'https://lab.example', 'JUDGELAB_PASSWORD': 'short'},
])
def test_hosted_configuration_fails_closed(environment):
    with pytest.raises(ValueError):
        hosted_settings(environment)


@pytest.fixture
def hosted_app(tmp_path):
    server = LabHTTPServer(('127.0.0.1', 0), Handler)
    server.public_origin, server.auth_digest = hosted_settings({
        'JUDGELAB_PUBLIC_ORIGIN': 'https://lab.example', 'JUDGELAB_PASSWORD': 'x'*32})
    server.store = Store(tmp_path / 'progress.json')
    server.token = 'csrf-token'
    server.run_lock = threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    status, _, headers = login_request(base)
    assert status == 303
    yield base, server, {'Host':'lab.example', 'Cookie':headers['Set-Cookie'].split(';')[0]}
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def test_every_hosted_asset_and_data_route_requires_login(hosted_app):
    base, _, headers = hosted_app
    for path in ('/', '/app.js', '/api/bootstrap', '/api/export', '/api/lesson/g-score'):
        status, body, response_headers = request(base, path, headers={'Host':'lab.example'})
        assert status == (200 if path == '/' else 401)
        assert 'WWW-Authenticate' not in response_headers
        if path == '/':
            assert b'autocomplete="current-password"' in body
        assert b'csrf-token' not in body
        assert request(base, path, headers=headers)[0] == 200


@pytest.mark.parametrize('authorization', ['Basic !!!', 'Bearer anything', 'Basic d3Jvbmc=', ''])
def test_invalid_authentication_is_rejected(hosted_app, authorization):
    base, _, headers = hosted_app
    assert request(base, '/api/bootstrap', headers={'Host':'lab.example','Authorization':authorization})[0] == 401


def test_hosted_auth_keeps_csrf_origin_and_host_guards(hosted_app):
    base, server, headers = hosted_app
    payload = {'accepted':True}
    assert request(base, '/api/consent', payload, {'Host':'lab.example','X-Lab-Token':'csrf-token'})[0] == 401
    assert request(base, '/api/consent', payload, headers)[0] == 403
    authenticated = {**headers, 'X-Lab-Token':'csrf-token'}
    assert request(base, '/api/consent', payload, {**authenticated,'Origin':'https://attacker.example'})[0] == 403
    assert request(base, '/api/consent', payload, {**authenticated,'Host':'attacker.example'})[0] == 403
    assert not server.store.state['consent']
    assert request(base, '/api/consent', payload, {**authenticated,'Origin':'https://lab.example'})[0] == 200
    assert server.store.state['consent']
    status, body, response_headers = request(base, '/api/bootstrap', headers=headers)
    assert status == 200
    assert json.loads(body)['hosted'] is True
    assert 'Strict-Transport-Security' in response_headers


def login_request(base, password='x'*32, origin='https://lab.example', username='learner'):
    connection = http.client.HTTPConnection(urlsplit(base).netloc)
    connection.request('POST', '/login', urlencode({'username':username, 'password':password}),
                       {'Host':'lab.example', 'Origin':origin,
                        'Content-Type':'application/x-www-form-urlencoded'})
    response = connection.getresponse()
    result = response.status, response.read(), dict(response.headers)
    connection.close()
    return result


def test_native_login_success_and_failure(hosted_app):
    base, _, _ = hosted_app
    status, _, headers = login_request(base)
    assert status == 303 and headers['Location'] == '/'
    for flag in ('Secure', 'HttpOnly', 'SameSite=Lax', 'Path=/', 'Max-Age=604800'):
        assert flag in headers['Set-Cookie']
    for username, password in [('learner', 'wrong'), ('other', 'x'*32)]:
        status, body, headers = login_request(base, password=password, username=username)
        assert status == 401
        assert b'role="alert"' in body
        assert headers['Referrer-Policy'] == 'same-origin'
        assert b'value="wrong"' not in body
        assert 'Set-Cookie' not in headers and 'WWW-Authenticate' not in headers
    assert login_request(base, origin='https://attacker.example')[0] == 403
    assert login_request(base, origin='null')[0] == 403
    for path in ('/login', '/login.css', '/favicon.svg'):
        assert request(base, path, headers={'Host':'lab.example'})[0] == 200


def test_session_tampering_expiry_and_password_change(hosted_app):
    base, server, headers = hosted_app
    assert request(base, '/api/bootstrap', headers={**headers, 'Cookie':headers['Cookie']+'x'})[0] == 401
    value = str(int(time.time()) - 1) + '.nonce'
    signature = hmac.new(server.auth_digest, ('judgelab-session-v1:' + server.public_origin + ':' + value).encode(), 'sha256').hexdigest()
    assert request(base, '/api/bootstrap', headers={**headers, 'Cookie':f'__Host-judgelab={value}.{signature}'})[0] == 401
    server.public_origin, server.auth_digest = hosted_settings({
        'JUDGELAB_PUBLIC_ORIGIN': 'https://lab.example', 'JUDGELAB_PASSWORD': 'y'*32})
    assert request(base, '/api/bootstrap', headers=headers)[0] == 401


def test_login_policy_preserves_native_form_origin(hosted_app):
    base, _, _ = hosted_app
    status, _, headers = request(base, '/login', headers={'Host':'lab.example'})
    assert status == 200
    # Native form POSTs under no-referrer send Origin: null, unlike fetch().
    policy = headers['Referrer-Policy']
    browser_origin = 'null' if policy == 'no-referrer' else 'https://lab.example'
    status, body, _ = login_request(base, origin=browser_origin)
    assert status == 303, body.decode()
    assert policy == 'same-origin'


def test_reveal_recovers_after_process_restart(hosted_app):
    base, server, headers = hosted_app
    server.store.state['attempts']['g-score'] = 1
    server.token = 'new-process-token'
    status, body, _ = request(base, '/api/reveal', {'id':'g-score'},
                              {**headers, 'X-Lab-Token':'csrf-token'})
    assert status == 403, body.decode()
    assert json.loads(body)['code'] == 'session_token_expired'
    status, body, _ = request(base, '/api/bootstrap', headers=headers)
    assert status == 200
    token = json.loads(body)['token']
    assert request(base, '/api/reveal', {'id':'g-score'},
                   {**headers, 'X-Lab-Token':token})[0] == 200
