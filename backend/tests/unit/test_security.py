"""
Unit tests for Security utilities & RBAC.
"""
import pytest
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.core.dependencies import require_role


def test_password_hashing():
    pw = "SuperSecurePassword123!"
    h = get_password_hash(pw)
    assert h != pw
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword", h) is False


def test_token_hash_deterministic():
    token = "some_sample_refresh_token_string"
    h1 = hash_token(token)
    h2 = hash_token(token)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_token_decode_invalid_type():
    access_tok = create_access_token("user-123", role="candidate")
    with pytest.raises(AuthenticationException) as exc:
        decode_token(access_tok, expected_type="refresh")
    assert "Invalid token type" in str(exc.value)


@pytest.mark.asyncio
async def test_require_role_rbac():
    admin_checker = require_role("admin")
    candidate_user = User(id="u1", name="Candidate", email="c@test.com", password_hash="x", role="candidate")
    admin_user = User(id="u2", name="Admin", email="a@test.com", password_hash="x", role="admin")

    # Candidate should fail admin check
    with pytest.raises(AuthorizationException):
        await admin_checker(current_user=candidate_user)

    # Admin should succeed
    res = await admin_checker(current_user=admin_user)
    assert res.id == "u2"
