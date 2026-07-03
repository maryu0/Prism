import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core.config import get_settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(*, user_id: str, workspace_id: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "workspaceId": workspace_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])


def generate_opaque_token() -> str:
    """Used for refresh tokens and invite tokens — random, unguessable, not a JWT."""
    return secrets.token_urlsafe(32)


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().fernet_key.encode("utf-8"))


def encrypt_secret(plaintext: str) -> str:
    """Used for GitHub PATs at rest — Fernet is symmetric encryption (not hashing,
    which is one-way): we need the plaintext token back later to actually call
    the GitHub API, so it must be reversible, unlike a password hash."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
