import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import (create_token, current_user, exchange_provider_code, hash_password,
                      provider_identity, provider_redirect, verify_password, _decode)
from app.config import FRONTEND_URL, OAUTH_PROVIDERS
from app.database import get_db
from app.models_db import User
from app.schemas import AuthResponse, Credentials, UserResponse

router = APIRouter()


def _response(user: User) -> AuthResponse:
    return AuthResponse(token=create_token(user), user=UserResponse(id=user.id, email=user.email, name=user.name))


@router.post('/auth/signup', response_model=AuthResponse)
def signup(credentials: Credentials, db: Session = Depends(get_db)):
    email = credentials.email.strip().lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        raise HTTPException(status_code=400, detail='Enter a valid email address.')
    if len(credentials.password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters.')
    if not credentials.name or len(credentials.name.strip()) < 2:
        raise HTTPException(status_code=400, detail='Enter your full name.')
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail='An account with this email already exists.')
    user = User(email=email, name=credentials.name.strip(), password_hash=hash_password(credentials.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _response(user)


@router.post('/auth/signin', response_model=AuthResponse)
def signin(credentials: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.strip().lower()).first()
    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Email or password is incorrect.')
    return _response(user)


@router.get('/auth/me', response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.get('/auth/{provider}', name='oauth_start')
def oauth_start(provider: str, request: Request):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=404, detail='Unsupported sign-in provider.')
    return RedirectResponse(provider_redirect(provider, request))


@router.get('/auth/{provider}/callback', name='oauth_callback')
async def oauth_callback(provider: str, request: Request, code: str, state: str, db: Session = Depends(get_db)):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=404, detail='Unsupported sign-in provider.')
    state_data = _decode(state)
    if state_data.get('provider') != provider:
        raise HTTPException(status_code=400, detail='Invalid OAuth state.')
    try:
        profile = await exchange_provider_code(provider, code, str(request.url_for('oauth_callback', provider=provider)))
        provider_id, name, email = provider_identity(provider, profile)
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Could not complete provider sign-in.') from exc
    user = db.query(User).filter(User.provider == provider, User.provider_id == provider_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        user = User(email=email.lower() if email else None, name=name, provider=provider, provider_id=provider_id)
        db.add(user)
    elif not user.provider_id:
        user.provider, user.provider_id = provider, provider_id
    db.commit()
    return RedirectResponse(f'{FRONTEND_URL}/auth/callback?token={create_token(user)}')
