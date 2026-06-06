from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError, VerificationError
from argon2.low_level import Type
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


ALGORITHM = "HS256"
ARGON2_HASHER = PasswordHasher(type=Type.ID)
LEGACY_BCRYPT_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return ARGON2_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$argon2"):
        try:
            return ARGON2_HASHER.verify(password_hash, password)
        except (InvalidHashError, VerifyMismatchError, VerificationError):
            return False

    if password_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return LEGACY_BCRYPT_CONTEXT.verify(password, password_hash)
        except (ValueError, TypeError):
            return False

    return False


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        token_type = payload.get("type")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        ) from exc

    if not subject or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",
        )
    return str(subject)
