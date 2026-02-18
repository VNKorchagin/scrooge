"""Tests for CSV export functionality."""
import pytest
import pytest_asyncio
import csv
import io
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base
from app.main import app
from app.services.transaction_service import TransactionService
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.models.user import User

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
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        username="testuser",
        hashed_password="hashed",
        currency="USD"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_transactions(db_session: AsyncSession, test_user: User):
    """Create test transactions with various field combinations."""
    transactions = []
    
    # Transaction with all fields
    t1 = Transaction(
        user_id=test_user.id,
        type=TransactionType.expense,
        amount=Decimal("100.50"),
        category_name="Food",
        description="Lunch",
        transaction_date=datetime(2026, 2, 15, 12, 0, 0),
        source=TransactionSource.manual,
        created_at=datetime(2026, 2, 15, 12, 0, 0)
    )
    transactions.append(t1)
    
    # Transaction without description
    t2 = Transaction(
        user_id=test_user.id,
        type=TransactionType.income,
        amount=Decimal("5000.00"),
        category_name="Salary",
        description=None,
        transaction_date=datetime(2026, 2, 1, 9, 0, 0),
        source=TransactionSource.manual,
        created_at=datetime(2026, 2, 1, 9, 0, 0)
    )
    transactions.append(t2)
    
    # Transaction without transaction_date (should not happen but test safety)
    t3 = Transaction(
        user_id=test_user.id,
        type=TransactionType.expense,
        amount=Decimal("50.00"),
        category_name="Transport",
        description="Taxi",
        transaction_date=None,
        source=TransactionSource.manual,
        created_at=datetime(2026, 2, 10, 15, 30, 0)
    )
    transactions.append(t3)
    
    for t in transactions:
        db_session.add(t)
    
    await db_session.commit()
    return transactions


class TestExportService:
    """Test export service method."""
    
    @pytest.mark.asyncio
    async def test_get_all_for_export(self, db_session: AsyncSession, test_user: User, test_transactions):
        """Test get_all_for_export returns all transactions."""
        result = await TransactionService.get_all_for_export(db_session, test_user.id)
        
        assert len(result) == 3
        # Should be ordered by transaction_date desc
        assert result[0].category_name == "Food"  # Feb 15
        assert result[1].category_name == "Transport"  # None (comes after dates)
        assert result[2].category_name == "Salary"  # Feb 1
    
    @pytest.mark.asyncio
    async def test_get_all_for_export_with_type_filter(self, db_session: AsyncSession, test_user: User, test_transactions):
        """Test get_all_for_export with type filter."""
        result = await TransactionService.get_all_for_export(
            db_session, test_user.id, type=TransactionType.income
        )
        
        assert len(result) == 1
        assert result[0].type == TransactionType.income
        assert result[0].category_name == "Salary"
    
    @pytest.mark.asyncio
    async def test_get_all_for_export_with_date_filter(self, db_session: AsyncSession, test_user: User, test_transactions):
        """Test get_all_for_export with date filter."""
        result = await TransactionService.get_all_for_export(
            db_session, test_user.id,
            date_from=datetime(2026, 2, 1, 0, 0, 0),
            date_to=datetime(2026, 2, 5, 23, 59, 59)
        )
        
        assert len(result) == 1
        assert result[0].category_name == "Salary"


class TestExportCSV:
    """Test CSV export endpoint."""
    
    def test_export_csv_with_data(self, client, auth_headers, test_transactions):
        """Test CSV export returns correct data format."""
        response = client.get("/v1/export/csv", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment; filename=transactions_" in response.headers["content-disposition"]
        
        # Parse CSV response
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header
        assert rows[0] == [
            "ID", "Type", "Amount", "Category", "Description",
            "Transaction Date", "Source", "Created At"
        ]
        
        # Check data rows (should have 3 transactions)
        assert len(rows) == 4  # header + 3 transactions
        
        # Check first transaction (with all fields)
        assert rows[1][1] == "expense"
        assert rows[1][2] == "100.5"
        assert rows[1][3] == "Food"
        assert rows[1][4] == "Lunch"
        assert "2026-02-15" in rows[1][5]  # Transaction Date
        assert rows[1][6] == "manual"
        
        # Check second transaction (without description)
        assert rows[2][4] == ""  # Description should be empty string
        
        # Check third transaction (without transaction_date)
        assert rows[3][5] == ""  # Transaction Date should be empty string
    
    def test_export_csv_with_date_filter(self, client, auth_headers, test_transactions):
        """Test CSV export with date range filter."""
        response = client.get(
            "/v1/export/csv?date_from=2026-02-01T00:00:00&date_to=2026-02-05T23:59:59",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Should only include Salary transaction (Feb 1)
        assert len(rows) == 2  # header + 1 transaction
        assert rows[1][3] == "Salary"
    
    def test_export_csv_with_type_filter(self, client, auth_headers, test_transactions):
        """Test CSV export with type filter."""
        response = client.get(
            "/v1/export/csv?type=income",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Should only include income transaction
        assert len(rows) == 2  # header + 1 income
        assert rows[1][1] == "income"
        assert rows[1][3] == "Salary"
    
    def test_export_csv_empty(self, client, auth_headers):
        """Test CSV export when no transactions exist."""
        response = client.get("/v1/export/csv", headers=auth_headers)
        
        assert response.status_code == 200
        
        content = response.content.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Should only have header row
        assert len(rows) == 1
        assert rows[0][0] == "ID"
    
    def test_export_csv_unauthorized(self, client):
        """Test CSV export without authentication fails."""
        response = client.get("/v1/export/csv")
        
        assert response.status_code == 401


# Fixtures for API tests
@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    from app.core.database import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Create authorization headers with valid token."""
    from app.core.security import create_access_token
    
    token = create_access_token({"sub": str(test_user.username)})
    return {"Authorization": f"Bearer {token}"}
