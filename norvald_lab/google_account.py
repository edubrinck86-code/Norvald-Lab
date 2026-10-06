"""Google identity for the local Lab. No Desk/Studio sessions or credentials travel."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
from pathlib import Path
import re
import secrets
from threading import RLock
import time
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

ISSUER = 'https://accounts.google.com'
USERINFO = 'https://openidconnect.googleapis.com/v1/userinfo'
TOKEN = 'https://oauth2.googleapis.com/token'
DRIVE_READ = 'https://www.googleapis.com/auth/drive.readonly'
DEFAULT_ROOT = '1oNz4GPdtpsrqMKwJlRZ-XTG1sDIfkdiK'


class GoogleAccount:
    def __init__(self, root: Path, *, port=8766, clock=time.time, transport=None):
        self.directory = root / 'private'
        self.path = self.directory / 'google-account.json'
        self.lock, self.clock, self.transport = RLock(), clock, transport
        if not 1 <= int(port) <= 65535:
            raise ValueError('Porta OAuth inválida.')
        self.redirect = f'http://127.0.0.1:{port}/api/account/google/callback'

    def read(self):
        return json.loads(self.path.read_text()) if self.path.exists() else {}

    def write(self, data):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory.chmod(0o700)
        temporary = self.directory / ('.google-' + uuid4().hex + '.tmp')
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, 'w') as output:
                json.dump(data, output, ensure_ascii=False)
            temporary.replace(self.path)
            self.path.chmod(0o600)
        finally:
            temporary.unlink(missing_ok=True)

    def credentials(self, data):
        saved = data.get('credentials', {})
        return {'client_id': os.environ.get('NORVALD_LAB_GOOGLE_CLIENT_ID', '') or saved.get('client_id', ''),
                'client_secret': os.environ.get('NORVALD_LAB_GOOGLE_CLIENT_SECRET', '') or saved.get('client_secret', '')}

    def status(self):
        with self.lock:
            data = self.read()
            session = data.get('session', {})
            owner = data.get('owner')
            return {'configured': bool(self.credentials(data)['client_id']),
                    'connected': bool(owner and (session.get('refresh_token') or session.get('expires_at', 0) > self.clock())),
                    'identity': owner, 'drive_read': DRIVE_READ in session.get('scopes', []),
                    'root_id': data.get('drive_root', {}).get('id', DEFAULT_ROOT),
                    'root_connected': bool(data.get('drive_root') and data['drive_root'].get('subject') == (owner or {}).get('subject')),
                    'credentials_source': 'environment' if os.environ.get('NORVALD_LAB_GOOGLE_CLIENT_ID') else 'local' if data.get('credentials') else 'none'}

    def configure(self, payload):
        with self.lock:
            data = self.read()
            if data.get('session'):
                raise ValueError('Desconecte o Google antes de trocar a configuração OAuth.')
            installed = payload.get('installed') if isinstance(payload, dict) else None
            if not isinstance(installed, dict):
                raise ValueError('Selecione o JSON de um cliente OAuth do tipo Desktop, como no Desk.')
            client = installed.get('client_id', '')
            secret = installed.get('client_secret', '')
            if not isinstance(client, str) or len(client) > 500 or not client.endswith('.apps.googleusercontent.com') or not isinstance(secret, str) or len(secret) > 1000:
                raise ValueError('Credenciais OAuth Desktop inválidas.')
            data['credentials'] = {'client_id': client, 'client_secret': secret}
            data.pop('pending', None)
            self.write(data)
        return self.status()

    def login(self, capability='identity'):
        if capability not in {'identity', 'drive_read'}:
            raise ValueError('Permissão Google não suportada.')
        with self.lock:
            data = self.read()
            credentials = self.credentials(data)
            if not credentials['client_id']:
                raise ValueError('Importe as credenciais Desktop em Settings para configurar o primeiro acesso.')
            verifier, state = secrets.token_urlsafe(64), secrets.token_urlsafe(32)
            scopes = ['openid', 'email', 'profile']
            if capability == 'drive_read' or DRIVE_READ in data.get('session', {}).get('scopes', []):
                scopes.append(DRIVE_READ)
            data['pending'] = {'state': state, 'verifier': verifier, 'expires_at': self.clock() + 600,
                               'scopes': scopes, 'client_id': credentials['client_id']}
            self.write(data)
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
            query = {'client_id': credentials['client_id'], 'redirect_uri': self.redirect, 'response_type': 'code',
                     'scope': ' '.join(scopes), 'state': state, 'code_challenge': challenge, 'code_challenge_method': 'S256',
                     'access_type': 'offline', 'prompt': 'consent select_account', 'include_granted_scopes': 'true'}
            if data.get('owner'):
                query['login_hint'] = data['owner']['subject']
        return {'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(query)}

    def request(self, method, url, **kwargs):
        with httpx.Client(timeout=30, follow_redirects=False, transport=self.transport) as client:
            response = client.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise PermissionError('Google recusou a autorização. Tente conectar novamente.')
        return response.json()

    def callback(self, code, state):
        with self.lock:
            data = self.read()
            pending = data.pop('pending', {})
            credentials = self.credentials(data)
            if (not isinstance(state, str) or not pending.get('state') or not secrets.compare_digest(state, pending['state'])
                or pending.get('expires_at', 0) < self.clock() or pending.get('client_id') != credentials['client_id']):
                # An invalid callback must not erase a still-valid login request.
                raise PermissionError('Pedido de login inválido ou expirado. Inicie novamente pelo Lab.')
            self.write(data)  # Single use, including failed exchanges.
            tokens = self.request('POST', TOKEN, data={**credentials, 'code': code, 'redirect_uri': self.redirect,
                'grant_type': 'authorization_code', 'code_verifier': pending['verifier']})
            token = tokens.get('access_token')
            if not isinstance(token, str) or not token:
                raise PermissionError('Google não retornou uma sessão válida.')
            profile = self.request('GET', USERINFO, headers={'Authorization': 'Bearer ' + token})
            subject = profile.get('sub')
            if (not isinstance(subject, str) or not subject.strip() or len(subject) > 255
                or profile.get('email_verified') is not True or not isinstance(profile.get('email'), str) or not profile['email']):
                raise PermissionError('Identidade Google não confirmada.')
            old = data.get('owner')
            if old and old['subject'] != subject:
                raise PermissionError('Esta pasta de dados do Lab está associada a outra conta Google. Desconecte e remova a associação antes de trocar.')
            data['owner'] = {'issuer': ISSUER, 'subject': subject, 'email': profile['email'], 'name': str(profile.get('name') or '')}
            previous = data.get('session', {}) if old and old['subject'] == subject else {}
            data['session'] = {'access_token': token, 'refresh_token': tokens.get('refresh_token') or previous.get('refresh_token', ''),
                'expires_at': self.clock() + float(tokens.get('expires_in', 3600)),
                'scopes': str(tokens.get('scope') or ' '.join(pending['scopes'])).split()}
            self.write(data)
        return self.status()

    def access_token(self):
        with self.lock:
            data = self.read()
            session = data.get('session', {})
            if not data.get('owner') or DRIVE_READ not in session.get('scopes', []):
                raise PermissionError('Autorize consulta ao Google Drive pelo Lab.')
            if session.get('access_token') and session.get('expires_at', 0) > self.clock() + 60:
                return session['access_token']
            if not session.get('refresh_token'):
                raise PermissionError('Conecte novamente o Google para renovar a sessão.')
            payload = self.request('POST', TOKEN, data={**self.credentials(data),
                'grant_type': 'refresh_token', 'refresh_token': session['refresh_token']})
            token = payload.get('access_token')
            if not token:
                raise PermissionError('Google não renovou a sessão.')
            session.update(access_token=token, expires_at=self.clock() + float(payload.get('expires_in', 3600)))
            self.write(data)
            return token

    def associate_root(self, value):
        root = str(value).strip().rsplit('/folders/', 1)[-1].split('?', 1)[0].strip('/')
        if not re.fullmatch('[A-Za-z0-9_-]{10,200}', root):
            raise ValueError('Informe o link ou ID da pasta do ecossistema.')
        with self.lock:
            token = self.access_token()
            row = self.request('GET', 'https://www.googleapis.com/drive/v3/files/' + root,
                params={'fields': 'id,name,mimeType,trashed'}, headers={'Authorization': 'Bearer ' + token})
            if row.get('trashed') or row.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError('O repositório precisa ser uma pasta ativa do Drive.')
            data = self.read()
            data['drive_root'] = {'id': root, 'subject': data['owner']['subject']}
            self.write(data)
        return self.status()

    def logout(self, *, forget=False):
        with self.lock:
            data = self.read()
            data.pop('session', None); data.pop('pending', None)
            if forget:
                data.pop('owner', None); data.pop('drive_root', None)
            self.write(data)
        return self.status()


def account_router(account):
    router = APIRouter(prefix='/api/account/google', tags=['google-account'])
    def checked(operation):
        try:
            return operation()
        except PermissionError as error:
            raise HTTPException(403, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            raise HTTPException(502, 'Não foi possível concluir a conexão com o Google. Seu conteúdo local foi preservado.') from error

    @router.get('')
    def status(): return account.status()

    @router.put('/configuration')
    def configure(payload: dict): return checked(lambda: account.configure(payload))

    @router.post('/login')
    def login(capability: str = 'identity'): return checked(lambda: account.login(capability))

    @router.get('/callback', response_class=HTMLResponse)
    def callback(code: str = '', state: str = '', error: str = ''):
        try:
            if error:
                raise PermissionError('A autorização foi cancelada no Google.')
            account.callback(code, state)
            message, success = 'Google conectado. Você pode fechar esta janela e voltar ao Lab.', True
        except Exception as exc:
            message, success = str(exc) if isinstance(exc, (ValueError, PermissionError)) else 'Não foi possível concluir a conexão com o Google.', False
        return HTMLResponse('<!doctype html><meta charset="utf-8"><title>Norvald Lab · Google</title>'
            '<body style="font-family:system-ui;background:#1d1a17;color:#d8c8ba;padding:48px"><h1>Norvald Lab</h1><p>'
            + html.escape(message) + '</p></body>', status_code=200 if success else 400)

    @router.put('/root')
    def root(payload: dict): return checked(lambda: account.associate_root(payload.get('root_id', '')))

    @router.post('/logout')
    def logout(): return account.logout()

    @router.delete('/association')
    def forget(): return account.logout(forget=True)

    return router
