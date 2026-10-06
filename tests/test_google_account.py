import json
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from norvald_lab.google_account import GoogleAccount, DRIVE_READ, DEFAULT_ROOT


def fixture_account(tmp_path):
    state = {'subject': 'stable-subject', 'email': 'owner@example.test', 'verified': True, 'calls': []}
    def handle(request):
        state['calls'].append(request)
        if request.url.path == '/token':
            return httpx.Response(200, json={'access_token': 'private-access', 'refresh_token': 'private-refresh', 'expires_in': 3600})
        if request.url.path.endswith('/userinfo'):
            return httpx.Response(200, json={'sub': state['subject'], 'email': state['email'], 'email_verified': state['verified']})
        return httpx.Response(200, json={'id': DEFAULT_ROOT, 'name': 'Norvald', 'mimeType': 'application/vnd.google-apps.folder'})
    account = GoogleAccount(tmp_path, port=8769, transport=httpx.MockTransport(handle))
    account.configure({'installed': {'client_id': 'example.apps.googleusercontent.com', 'client_secret': 'desktop-client-value'}})
    return account, state


def connect(account, capability='identity'):
    query = parse_qs(urlsplit(account.login(capability)['authorization_url']).query)
    return account.callback('one-time-code', query['state'][0])


def test_pkce_verified_subject_private_storage_and_custom_port(tmp_path):
    account, state = fixture_account(tmp_path)
    query = parse_qs(urlsplit(account.login()['authorization_url']).query)
    assert query['code_challenge_method'] == ['S256']
    assert query['redirect_uri'] == ['http://127.0.0.1:8769/api/account/google/callback']
    status = account.callback('code', query['state'][0])
    assert status['identity']['subject'] == 'stable-subject'
    assert status['identity']['issuer'] == 'https://accounts.google.com'
    sent = parse_qs(state['calls'][0].content.decode())
    assert sent['code_verifier'][0]
    assert 'private-access' not in json.dumps(status)
    assert 'private-refresh' not in json.dumps(status)
    assert account.path.stat().st_mode & 0o777 == 0o600
    assert account.directory.stat().st_mode & 0o777 == 0o700
    assert GoogleAccount(tmp_path).status()['identity'] == status['identity']


def test_invalid_state_preserves_pending_and_valid_state_is_single_use(tmp_path):
    account, _ = fixture_account(tmp_path)
    query = parse_qs(urlsplit(account.login()['authorization_url']).query)
    with pytest.raises(PermissionError): account.callback('code', 'forged')
    account.callback('code', query['state'][0])
    with pytest.raises(PermissionError): account.callback('code', query['state'][0])


def test_same_email_different_subject_cannot_reuse_account_or_root(tmp_path):
    account, state = fixture_account(tmp_path)
    connect(account, 'drive_read')
    account.associate_root(DEFAULT_ROOT)
    state['subject'] = 'different-subject'
    with pytest.raises(PermissionError, match='outra conta'): connect(account)
    status = account.status()
    assert status['identity']['subject'] == 'stable-subject'
    assert status['root_connected']


def test_logout_preserves_binding_forget_removes_it_without_touching_work(tmp_path):
    account, _ = fixture_account(tmp_path)
    marker = tmp_path / 'research.txt'; marker.write_text('Minha tese')
    connect(account)
    assert account.logout()['identity']['subject'] == 'stable-subject'
    assert not account.status()['connected']
    assert account.logout(forget=True)['identity'] is None
    assert marker.read_text() == 'Minha tese'


def test_unverified_identity_and_web_credentials_are_rejected(tmp_path):
    account, state = fixture_account(tmp_path)
    state['verified'] = False
    with pytest.raises(PermissionError): connect(account)
    assert account.status()['identity'] is None
    with pytest.raises(ValueError): account.configure({'web': {'client_id': 'example.apps.googleusercontent.com'}})


def test_drive_root_requires_capability_and_folder_validation(tmp_path):
    account, _ = fixture_account(tmp_path)
    connect(account)
    with pytest.raises(PermissionError): account.associate_root(DEFAULT_ROOT)
    connect(account, 'drive_read')
    status = account.associate_root('https://drive.google.com/drive/folders/' + DEFAULT_ROOT)
    assert status['root_connected'] and status['drive_read']


def test_account_routes_reject_foreign_origin_and_cross_site_posts(tmp_path):
    from fastapi.testclient import TestClient
    from norvald_lab.api import create_app
    app = create_app(tmp_path)
    with TestClient(app) as client:
        assert client.post('/api/account/google/login', headers={'Origin': 'https://outside.test'}).status_code == 403
        assert client.post('/api/account/google/logout', headers={'sec-fetch-site': 'cross-site'}).status_code == 403
        assert client.get('/api/account/google').status_code == 200
