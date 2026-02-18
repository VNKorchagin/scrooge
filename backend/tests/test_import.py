"""Tests for import functionality."""
import pytest
import pytest_asyncio
import pandas as pd
import io
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models first to ensure SQLAlchemy can resolve relationships
from app.models.vault import VaultAccount, VaultSnapshot, VaultProjectionSettings
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.models.user import User
from app.models.category import Category
from app.models.transaction_pattern import TransactionPattern
from app.models.mcc_code import MCCCode

from app.core.database import Base
from app.services.import_service import ImportService, ParsedTransaction, TinkoffAdapter, SberAdapter, AlfaAdapter, GenericAdapter
from app.services.categorization_service import CategorizationService
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService

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
    await init_db()
    async with TestingSessionLocal() as session:
        yield session
    await drop_db()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session):
    """Create a test user."""
    user = User(username="testuser", hashed_password="hash", language="ru")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestTinkoffAdapter:
    """Test Tinkoff Bank CSV adapter."""

    def test_detect_tinkoff_csv(self):
        """Test detection of Tinkoff CSV format."""
        columns = ['Дата операции', 'Дата платежа', 'Номер карты', 'Статус', 
                   'Сумма операции', 'Валюта операции', 'Описание', 'Категория']
        df = pd.DataFrame(columns=columns)
        assert TinkoffAdapter.detect(df) is True

    def test_detect_non_tinkoff_csv(self):
        """Test that non-Tinkoff CSV is not detected."""
        columns = ['Date', 'Amount', 'Description']
        df = pd.DataFrame(columns=columns)
        assert TinkoffAdapter.detect(df) is False

    def test_parse_tinkoff_transaction(self):
        """Test parsing Tinkoff transaction."""
        data = {
            'дата операции': ['31.01.2026 18:58:44'],
            'дата платежа': ['31.01.2026'],
            'номер карты': ['*1234'],
            'статус': ['OK'],
            'сумма операции': ['-500.00'],
            'валюта операции': ['RUB'],
            'описание': ['PYATYOROCHKA'],
            'категория': ['Супермаркеты'],
            'mcc': [5411.0],
        }
        df = pd.DataFrame(data)
        transactions = TinkoffAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].raw_description == 'PYATYOROCHKA'
        assert transactions[0].amount == Decimal('500.00')
        assert transactions[0].type == TransactionType.EXPENSE
        assert transactions[0].mcc_code == '5411'

    def test_parse_tinkoff_income(self):
        """Test parsing Tinkoff income transaction."""
        data = {
            'дата операции': ['31.01.2026 18:58:44'],
            'дата платежа': ['31.01.2026'],
            'номер карты': ['*1234'],
            'статус': ['OK'],
            'сумма операции': ['50000.00'],
            'валюта операции': ['RUB'],
            'описание': ['Зарплата'],
            'категория': ['Пополнения'],
            'mcc': [None],
        }
        df = pd.DataFrame(data)
        transactions = TinkoffAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.INCOME
        assert transactions[0].amount == Decimal('50000.00')

    def test_skip_failed_transactions(self):
        """Test that failed transactions are skipped."""
        data = {
            'дата операции': ['31.01.2026'],
            'дата платежа': ['31.01.2026'],
            'номер карты': ['*1234'],
            'статус': ['FAILED'],
            'сумма операции': ['-500.00'],
            'валюта операции': ['RUB'],
            'описание': ['Failed transaction'],
            'категория': ['Test'],
        }
        df = pd.DataFrame(data)
        transactions = TinkoffAdapter.parse(df)
        
        assert len(transactions) == 0


class TestSberAdapter:
    """Test SberBank CSV adapter."""

    def test_detect_sber_csv(self):
        """Test detection of Sber CSV format."""
        columns = ['Дата', 'Сумма', 'Описание']
        df = pd.DataFrame(columns=columns)
        assert SberAdapter.detect(df) is True

    def test_parse_sber_expense(self):
        """Test parsing Sber expense with negative sign."""
        data = {
            'дата': ['31.01.2026'],
            'сумма': ['-1000.00'],
            'описание': ['Магазин'],
        }
        df = pd.DataFrame(data)
        transactions = SberAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.EXPENSE
        assert transactions[0].amount == Decimal('1000.00')

    def test_parse_sber_income(self):
        """Test parsing Sber income with positive sign."""
        data = {
            'дата': ['31.01.2026'],
            'сумма': ['+5000.00'],
            'описание': ['Перевод'],
        }
        df = pd.DataFrame(data)
        transactions = SberAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.INCOME


class TestAlfaAdapter:
    """Test Alfa-Bank CSV adapter."""

    def test_detect_alfa_csv(self):
        """Test detection of Alfa CSV format."""
        columns = ['Дата', 'Приход', 'Расход', 'Описание']
        df = pd.DataFrame(columns=columns)
        assert AlfaAdapter.detect(df) is True

    def test_parse_alfa_expense(self):
        """Test parsing Alfa expense."""
        data = {
            'дата': ['31.01.2026'],
            'приход': [0],
            'расход': [1500.00],
            'описание': ['Кафе'],
        }
        df = pd.DataFrame(data)
        transactions = AlfaAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.EXPENSE
        assert transactions[0].amount == Decimal('1500.00')

    def test_parse_alfa_income(self):
        """Test parsing Alfa income."""
        data = {
            'дата': ['31.01.2026'],
            'приход': [100000.00],
            'расход': [0],
            'описание': ['Зарплата'],
        }
        df = pd.DataFrame(data)
        transactions = AlfaAdapter.parse(df)
        
        assert len(transactions) == 1
        assert transactions[0].type == TransactionType.INCOME


class TestImportService:
    """Test ImportService functionality."""

    def test_detect_adapter_tinkoff(self):
        """Test adapter detection for Tinkoff."""
        columns = ['Дата операции', 'Сумма операции', 'Описание', 'Категория']
        df = pd.DataFrame(columns=columns)
        adapter = ImportService.detect_adapter(df)
        assert adapter == TinkoffAdapter

    def test_parse_csv_with_tab_separator(self):
        """Test parsing TSV file."""
        csv_content = "Дата операции\tСумма операции\tОписание\tКатегория\tMCC\n31.01.2026\t-500.00\tМагазин\tСупермаркеты\t5411"
        content = csv_content.encode('utf-8')
        transactions, adapter_name = ImportService.parse_csv(content, "test.csv")
        
        assert len(transactions) == 1
        assert transactions[0].raw_description == 'Магазин'


class TestCategorizationService:
    """Test transaction categorization."""

    @pytest.mark.asyncio
    async def test_categorize_with_mcc(self, db_session, test_user):
        """Test categorization using MCC code."""
        # Create MCC code
        mcc = MCCCode(
            code="5411",
            name_en="Grocery Stores",
            name_ru="Продуктовые магазины",
            suggested_category_en="Groceries",
            suggested_category_ru="Продукты"
        )
        db_session.add(mcc)
        await db_session.commit()
        
        service = CategorizationService(db_session)
        result = await service.categorize(
            user_id=test_user.id,
            raw_description="TEST SHOP",
            mcc_code="5411",
            language="ru"
        )
        
        assert result["category"] == "Продукты"
        assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_categorize_with_regex_pattern(self, db_session, test_user):
        """Test categorization using regex patterns."""
        service = CategorizationService(db_session)
        result = await service.categorize(
            user_id=test_user.id,
            raw_description="Пятерочка магазин",
            mcc_code=None,
            language="ru"
        )
        
        assert result["category"] == "Продукты"
        assert result["confidence"] == "medium"

    @pytest.mark.asyncio
    async def test_categorize_unknown(self, db_session, test_user):
        """Test categorization for unknown merchant."""
        service = CategorizationService(db_session)
        result = await service.categorize(
            user_id=test_user.id,
            raw_description="UNKNOWN_MERCHANT_XYZ",
            mcc_code=None,
            language="ru"
        )
        
        assert result["category"] == "Другое"
        assert result["confidence"] == "low"

    @pytest.mark.asyncio
    async def test_learn_pattern(self, db_session, test_user):
        """Test learning user pattern."""
        service = CategorizationService(db_session)
        
        # Create category
        category = Category(name="Моя категория", user_id=test_user.id)
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        # Learn pattern
        pattern = await service.learn_pattern(
            user_id=test_user.id,
            raw_description="UNIQUE_SHOP_123",
            category_name="Моя категория",
            category_id=category.id
        )
        
        assert pattern is not None
        assert pattern.normalized_pattern == "unique_shop_123"
        assert pattern.usage_count == 1
        
        # Verify pattern works
        result = await service.categorize(
            user_id=test_user.id,
            raw_description="UNIQUE_SHOP_123",
            mcc_code=None,
            language="ru"
        )
        
        assert result["category"] == "Моя категория"
        assert result["confidence"] == "high"


class TestDuplicateDetection:
    """Test duplicate transaction detection."""

    @pytest.mark.asyncio
    async def test_find_duplicates_by_description_and_amount(self, db_session, test_user):
        """Test finding duplicates by description and amount."""
        # Create existing transaction
        tx = Transaction(
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            category_name="Продукты",
            description="PYATYOROCHKA",
            raw_description="PYATYOROCHKA 6431 MOSCOW",
            transaction_date=datetime(2026, 1, 31, 18, 58, 44),
            source=TransactionSource.MANUAL
        )
        db_session.add(tx)
        await db_session.commit()
        
        # Search for duplicate
        duplicates = await TransactionService.find_duplicates(
            db_session,
            test_user.id,
            "PYATYOROCHKA",
            Decimal("500.00"),
            datetime(2026, 1, 31, 18, 58, 44)
        )
        
        assert len(duplicates) == 1
        assert duplicates[0].raw_description == "PYATYOROCHKA 6431 MOSCOW"

    @pytest.mark.asyncio
    async def test_no_duplicates_for_different_amount(self, db_session, test_user):
        """Test that different amounts are not duplicates."""
        # Create existing transaction
        tx = Transaction(
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            category_name="Продукты",
            description="PYATYOROCHKA",
            transaction_date=datetime(2026, 1, 31),
            source=TransactionSource.MANUAL
        )
        db_session.add(tx)
        await db_session.commit()
        
        # Search with different amount
        duplicates = await TransactionService.find_duplicates(
            db_session,
            test_user.id,
            "PYATYOROCHKA",
            Decimal("1000.00"),
            datetime(2026, 1, 31)
        )
        
        assert len(duplicates) == 0

    @pytest.mark.asyncio
    async def test_duplicate_detection_in_import(self, db_session, test_user):
        """Test duplicate detection during import preview."""
        # Create existing transaction
        tx = Transaction(
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            category_name="Продукты",
            description="AQUA",
            raw_description="https://aquatime.veel.shop",
            transaction_date=datetime(2026, 1, 31, 18, 58, 44),
            source=TransactionSource.MANUAL
        )
        db_session.add(tx)
        await db_session.commit()
        
        # Create parsed transaction
        parsed_tx = ParsedTransaction(
            raw_description="https://aquatime.veel.shop",
            amount=Decimal("500.00"),
            transaction_date=datetime(2026, 1, 31, 18, 58, 44),
            type=TransactionType.EXPENSE
        )
        
        # Check for duplicates
        transactions = await ImportService.check_duplicates(
            [parsed_tx],
            test_user.id,
            db_session
        )
        
        assert transactions[0].is_duplicate is True
        assert transactions[0].duplicate_count == 1


class TestImportIntegration:
    """Integration tests for import functionality."""

    @pytest.mark.asyncio
    async def test_full_import_flow(self, db_session, test_user):
        """Test complete import flow from CSV to saved transactions."""
        # Create CSV content
        csv_content = """Дата операции	Сумма операции	Описание	Категория	MCC
31.01.2026 18:58:44	-500.00	Магазин	Супермаркеты	5411
31.01.2026 19:00:00	100000.00	Зарплата	Пополнения	"""
        
        # Parse CSV
        content = csv_content.encode('utf-8')
        transactions, adapter_name = ImportService.parse_csv(content, "tinkoff.csv")
        
        assert len(transactions) == 2
        assert adapter_name == "TinkoffAdapter"
        
        # Categorize
        transactions = await ImportService.categorize_transactions(
            transactions,
            test_user.id,
            db_session,
            "ru"
        )
        
        # Verify categorization
        assert transactions[0].suggested_category is not None
        assert transactions[1].suggested_category is not None
        
        # Create transactions in DB
        for tx_data in transactions:
            category = await CategoryService.get_or_create(
                db_session, tx_data.suggested_category or "Другое", test_user.id
            )
            tx = Transaction(
                user_id=test_user.id,
                type=tx_data.type or TransactionType.EXPENSE,
                amount=tx_data.amount,
                category_id=category.id,
                category_name=category.name,
                description=tx_data.raw_description[:100],
                raw_description=tx_data.raw_description,
                transaction_date=tx_data.transaction_date or datetime.now(),
                source=TransactionSource.IMPORT_CSV
            )
            db_session.add(tx)
        
        await db_session.commit()
        
        # Verify transactions were created
        result = await db_session.execute(
            select(Transaction).where(Transaction.user_id == test_user.id)
        )
        saved_transactions = result.scalars().all()
        
        assert len(saved_transactions) == 2
        assert all(tx.source == TransactionSource.IMPORT_CSV for tx in saved_transactions)
