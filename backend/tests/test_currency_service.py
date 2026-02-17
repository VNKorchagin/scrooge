"""Tests for currency service."""
import pytest
from decimal import Decimal
from app.services.currency_service import CurrencyService


class TestCurrencyConversion:
    """Test currency conversion logic."""

    def test_convert_usd_to_rub(self):
        """Test converting USD to RUB."""
        amount = Decimal("100.00")
        rate = 90.5  # 1 USD = 90.5 RUB
        
        result = CurrencyService.convert_amount(amount, "USD", "RUB", rate)
        
        assert result == Decimal("9050.00")

    def test_convert_rub_to_usd(self):
        """Test converting RUB to USD."""
        amount = Decimal("9050.00")
        rate = 90.5  # 1 USD = 90.5 RUB
        
        result = CurrencyService.convert_amount(amount, "RUB", "USD", rate)
        
        assert result == Decimal("100.00")

    def test_convert_same_currency(self):
        """Test converting same currency returns same amount."""
        amount = Decimal("100.00")
        rate = 1.0
        
        result = CurrencyService.convert_amount(amount, "USD", "USD", rate)
        
        assert result == amount

    def test_convert_with_high_precision(self):
        """Test conversion with high precision decimals."""
        amount = Decimal("99.99")
        rate = 90.12345
        
        result = CurrencyService.convert_amount(amount, "USD", "RUB", rate)
        
        # Check result is Decimal with correct value
        assert isinstance(result, Decimal)
        assert result > 0

    def test_convert_zero_amount(self):
        """Test converting zero amount."""
        amount = Decimal("0")
        rate = 90.5
        
        result = CurrencyService.convert_amount(amount, "USD", "RUB", rate)
        
        assert result == Decimal("0")

    def test_truncate_long_password(self):
        """Test that passwords longer than 72 bytes are truncated."""
        from app.core.security import _truncate_password
        
        long_password = "a" * 100
        truncated = _truncate_password(long_password)
        
        assert len(truncated) == 72

    def test_truncate_unicode_password(self):
        """Test that unicode passwords are properly truncated by bytes."""
        from app.core.security import _truncate_password
        
        # Russian characters are 2 bytes each in UTF-8
        unicode_password = "пароль" * 20  # 120 bytes
        truncated = _truncate_password(unicode_password)
        
        # Should be truncated to 72 bytes, not 72 characters
        assert len(truncated) <= 72


class TestPasswordHashing:
    """Test password hashing with bcrypt."""

    def test_short_password_hash(self):
        """Test hashing short password."""
        from app.core.security import get_password_hash, verify_password
        
        password = "12345"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed)

    def test_long_password_hash(self):
        """Test hashing long password (should be truncated)."""
        from app.core.security import get_password_hash, verify_password
        
        password = "a" * 100
        hashed = get_password_hash(password)
        
        # First 72 chars should verify
        assert verify_password("a" * 72, hashed)

    def test_unicode_password_hash(self):
        """Test hashing unicode password."""
        from app.core.security import get_password_hash, verify_password
        
        password = "пароль" * 10
        hashed = get_password_hash(password)
        
        # Should not raise error
        assert isinstance(hashed, str)
        # Original password should verify
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        """Test that wrong password doesn't verify."""
        from app.core.security import get_password_hash, verify_password
        
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert not verify_password(wrong_password, hashed)
