"""Tests for transaction service."""
import pytest
from decimal import Decimal
from datetime import datetime
from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction, TransactionType, TransactionSource


class TestTransactionCreation:
    """Test transaction creation."""

    @pytest.mark.asyncio
    async def test_create_transaction_with_string_type(self, db_session):
        """Test creating transaction with string type (from API)."""
        from app.schemas.transaction import TransactionCreate
        from app.services.category_service import CategoryService
        
        # Create a user first
        from app.models.user import User
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        
        # Create transaction data with string type (as it comes from API)
        transaction_data = TransactionCreate(
            type="expense",  # String as it comes from API
            amount=Decimal("15.00"),
            category_name="Продукты",
            transaction_date=datetime.now()
        )
        
        # Create transaction
        transaction = await TransactionService.create(
            db_session, transaction_data, user.id
        )
        
        # Verify
        assert transaction is not None
        assert transaction.type == TransactionType.EXPENSE
        assert transaction.amount == Decimal("15.00")
        assert transaction.category_name == "Продукты"
        assert transaction.source == TransactionSource.MANUAL
        assert transaction.user_id == user.id

    @pytest.mark.asyncio
    async def test_create_transaction_with_enum_type(self, db_session):
        """Test creating transaction with enum type."""
        from app.schemas.transaction import TransactionCreate
        from app.models.user import User
        
        # Create a user
        user = User(username="testuser2", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        
        # Create transaction data with enum type
        transaction_data = TransactionCreate(
            type=TransactionType.INCOME,
            amount=Decimal("100.00"),
            category_name="Зарплата",
            transaction_date=datetime.now()
        )
        
        # Create transaction
        transaction = await TransactionService.create(
            db_session, transaction_data, user.id
        )
        
        # Verify
        assert transaction is not None
        assert transaction.type == TransactionType.INCOME
        assert transaction.amount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_create_transaction_creates_category(self, db_session):
        """Test that creating transaction creates new category if not exists."""
        from app.schemas.transaction import TransactionCreate
        from app.models.user import User
        from app.services.category_service import CategoryService
        
        # Create a user
        user = User(username="testuser3", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        
        # Create transaction with new category
        transaction_data = TransactionCreate(
            type="expense",
            amount=Decimal("25.00"),
            category_name="NewCategory",
            transaction_date=datetime.now()
        )
        
        # Create transaction
        transaction = await TransactionService.create(
            db_session, transaction_data, user.id
        )
        
        # Verify category was created
        category = await CategoryService.get_by_name(
            db_session, "NewCategory", user.id
        )
        assert category is not None
        assert category.name == "NewCategory"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
        # Rollback after test
        await session.rollback()
