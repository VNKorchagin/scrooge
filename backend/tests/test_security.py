"""Tests for security module."""
import pytest
from app.core.security import get_password_hash, verify_password


class TestPasswordHashing:
    """Test password hashing with bcrypt."""

    def test_short_password(self):
        """Test hashing short password (normal case)."""
        password = "12345"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_medium_password(self):
        """Test hashing medium length password."""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_long_password_72_bytes(self):
        """Test password exactly at 72 bytes limit."""
        password = "a" * 72  # 72 ASCII chars = 72 bytes
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_very_long_password(self):
        """Test password longer than 72 bytes (should be truncated)."""
        password = "a" * 100  # 100 chars, will be truncated to 72
        hashed = get_password_hash(password)
        # First 72 chars should work
        assert verify_password("a" * 72, hashed)

    def test_long_password_with_unicode(self):
        """Test password with unicode characters."""
        # Russian characters take 2 bytes each in UTF-8
        password = "пароль" * 20  # 12 chars * 2 bytes = 120 bytes
        hashed = get_password_hash(password)
        # Should not raise ValueError
        assert isinstance(hashed, str)
        # Verification should work
        assert verify_password(password, hashed)

    def test_verify_truncated_password(self):
        """Test that verification works with truncated passwords."""
        long_password = "x" * 100
        short_password = "x" * 72
        
        # Hash long password (will be truncated)
        hashed = get_password_hash(long_password)
        
        # Both should verify correctly
        assert verify_password(long_password, hashed)
        assert verify_password(short_password, hashed)


class TestJWT:
    """Test JWT token operations."""

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        from app.core.security import decode_token
        
        invalid_token = "invalid.token.here"
        decoded = decode_token(invalid_token)
        
        assert decoded is None
    
    def test_decode_malformed_token(self):
        """Test decoding malformed token returns None."""
        from app.core.security import decode_token
        
        malformed_tokens = [
            "",
            "not.a.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # только header
            "invalid",
        ]
        
        for token in malformed_tokens:
            decoded = decode_token(token)
            assert decoded is None
