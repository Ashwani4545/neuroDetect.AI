import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import AUTH_SECRET, AUTH_TOKEN_DAYS, FRONTEND_URL, OAUTH_PROVIDERS
from app.database import get_db
from app.models_db import User


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f'{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_text, digest_text = encoded.split('$', 1)
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    signature = hmac.new(AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return f'{body}.{base64.urlsafe_b64encode(signature).decode().rstrip("=")}'


def _decode(token: str) -> dict:
    try:
        body, signature = token.split('.', 1)
        expected = hmac.new(AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
        if not hmac.compare_digest(supplied, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body + '=' * (-len(body) % 4)))
        if payload['exp'] < int(time.time()):
            raise ValueError
        return payload
    except (KeyError, ValueError, TypeError, binascii.Error, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail='Your session is invalid or expired.') from None


def create_token(user: User) -> str:
    return _sign({'sub': user.id, 'exp': int(time.time()) + AUTH_TOKEN_DAYS * 86400})


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get('Authorization', '')
    token = header[7:] if header.startswith('Bearer ') else request.query_params.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail='Sign in to access this resource.')
    user = db.query(User).filter(User.id == _decode(token)['sub']).first()
    if user is None:
        raise HTTPException(status_code=401, detail='Your account no longer exists.')
    return user


def provider_redirect(provider: str, request: Request) -> str:
    settings = OAUTH_PROVIDERS[provider]
    if not settings['client_id'] or not settings['client_secret']:
        raise HTTPException(status_code=503, detail=f'{provider.title()} sign-in is not configured on this server.')
    state = _sign({'provider': provider, 'nonce': secrets.token_urlsafe(16), 'exp': int(time.time()) + 600})
    callback = str(request.url_for('oauth_callback', provider=provider))
    params = {'client_id': settings['client_id'], 'redirect_uri': callback, 'response_type': 'code',
              'scope': settings['scope'], 'state': state}
    return f"{settings['authorize_url']}?{urlencode(params)}"


async def exchange_provider_code(provider: str, code: str, redirect_uri: str) -> dict:
    settings = OAUTH_PROVIDERS[provider]
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(settings['token_url'], data={
            'client_id': settings['client_id'], 'client_secret': settings['client_secret'],
            'code': code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code',
        }, headers={'Accept': 'application/json'})
        response.raise_for_status()
        token = response.json()['access_token']
        profile = await client.get(settings['userinfo_url'], headers={'Authorization': f'Bearer {token}'})
        profile.raise_for_status()
        return profile.json()


def provider_identity(provider: str, profile: dict) -> tuple[str, str, str | None]:
    provider_id = str(profile.get('id') or profile.get('sub') or '')
    email = profile.get('email')
    name = profile.get('name') or profile.get('given_name') or profile.get('username') or 'NeuroDetect user'
    if not provider_id:
        raise HTTPException(status_code=400, detail='The provider did not return a usable account identifier.')
    return provider_id, name, email
