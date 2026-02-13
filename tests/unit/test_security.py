"""
Test Security Utilities
"""
import pytest
from datetime import timedelta

from backend.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    is_token_expired
)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_hash_password(self):
        """Should hash password"""
        password = "test123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        """Should verify correct password"""
        password = "test123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Should reject incorrect password"""
        password = "test123"
        hashed = get_password_hash(password)
        assert verify_password("wrong", hashed) is False

    def test_same_password_different_hashes(self):
        """Should produce different hashes for same password (salt)"""
        password = "test123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestJWT:
    """Test JWT token functions"""

    def test_create_token(self):
        """Should create valid JWT token"""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_token(self):
        """Should decode valid token"""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"

    def test_decode_invalid_token(self):
        """Should return None for invalid token"""
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_token_expiration(self):
        """Should handle token expiration"""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        assert is_token_expired(token) is True

    def test_token_not_expired(self):
        """Should recognize valid non-expired token"""
        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        assert is_token_expired(token) is False
