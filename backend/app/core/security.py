"""
Security Utilities: Password Hashing & JWT Token Cryptography.
Uses Argon2/bcrypt for password hashing and PyJWT for signed JWTs.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationException

# CryptContext configured with argon2 with bcrypt fallback
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify raw password against stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password using Argon2/bcrypt."""
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    """Create a SHA256 digest of refresh tokens before storing in database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    role: str = "candidate",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate signed JWT access token with unique JTI."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT refresh token with unique JTI."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate signature, expiration, and token type."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationException(f"Invalid token type: expected {expected_type}, got {token_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationException(f"Invalid authentication token: {str(e)}")
