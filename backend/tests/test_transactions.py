"""Tests for transaction service."""
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.models.user import User
from app.schemas.transaction import TransactionCreate

# Create test database engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a test database session with tables."""
    # Create tables first
    await init_db()
    
    # Create session
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop tables after test
    await drop_db()


class TestTransactionCreation:
    """Test transaction creation."""

    @pytest.mark.asyncio
    async def test_create_transaction_with_string_type(self, db_session):
        """Test creating transaction with string type (from API)."""
        # Create a user first
        user = User(username="testuser", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
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
        # Create a user
        user = User(username="testuser2", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
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
        from app.services.category_service import CategoryService
        
        # Create a user
        user = User(username="testuser3", hashed_password="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
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
