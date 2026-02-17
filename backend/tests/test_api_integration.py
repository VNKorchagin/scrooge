"""Integration tests for API endpoints."""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.core.security import create_access_token, get_password_hash


# Test database
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with overridden database."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        hashed_password=get_password_hash("password123"),
        language="en",
        currency="USD",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user: User) -> str:
    """Create access token for test user."""
    return create_access_token({"sub": test_user.id})


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {test_user_token}"}


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        """Test user registration."""
        response = await client.post("/v1/auth/register", json={
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        response = await client.post("/v1/auth/register", json={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login."""
        response = await client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = await client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client, auth_headers, test_user):
        """Test getting current user info."""
        response = await client.get("/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client):
        """Test getting user info without token."""
        response = await client.get("/v1/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_user_settings(self, client, auth_headers, test_user, db_session):
        """Test updating user language and currency."""
        response = await client.patch("/v1/auth/me", headers=auth_headers, json={
            "language": "ru",
            "currency": "RUB"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "ru"
        assert data["currency"] == "RUB"


class TestTransactionEndpoints:
    """Test transaction endpoints."""

    @pytest.mark.asyncio
    async def test_create_transaction(self, client, auth_headers, test_user, db_session):
        """Test creating a transaction."""
        response = await client.post("/v1/transactions", headers=auth_headers, json={
            "type": "expense",
            "amount": 50.00,
            "category_name": "Food",
            "transaction_date": datetime.now().isoformat(),
            "description": "Lunch"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "expense"
        assert float(data["amount"]) == 50.00
        assert data["category_name"] == "Food"

    @pytest.mark.asyncio
    async def test_create_transaction_with_string_type(self, client, auth_headers):
        """Test creating transaction with string type (from frontend)."""
        response = await client.post("/v1/transactions", headers=auth_headers, json={
            "type": "income",
            "amount": 100.00,
            "category_name": "Salary",
            "transaction_date": datetime.now().isoformat()
        })
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "income"

    @pytest.mark.asyncio
    async def test_list_transactions(self, client, auth_headers, test_user, db_session):
        """Test listing transactions."""
        # Create a transaction first
        transaction = Transaction(
            user_id=test_user.id,
            type=TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            category_name="Test",
            category_id=None,
            transaction_date=datetime.now(),
            source=TransactionSource.MANUAL
        )
        db_session.add(transaction)
        await db_session.commit()
        
        response = await client.get("/v1/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_transactions_with_filters(self, client, auth_headers):
        """Test listing transactions with type filter."""
        response = await client.get(
            "/v1/transactions?type=expense&limit=10&offset=0",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_transactions_limit_validation(self, client, auth_headers):
        """Test that limit > 100 is rejected."""
        response = await client.get(
            "/v1/transactions?limit=10000",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error


class TestCategoryEndpoints:
    """Test category endpoints."""

    @pytest.mark.asyncio
    async def test_create_category(self, client, auth_headers):
        """Test creating a category."""
        response = await client.post("/v1/categories", headers=auth_headers, json={
            "name": "NewCategory"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NewCategory"

    @pytest.mark.asyncio
    async def test_list_categories(self, client, auth_headers):
        """Test listing categories."""
        response = await client.get("/v1/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_search_categories(self, client, auth_headers):
        """Test searching categories."""
        response = await client.get("/v1/categories?q=Food", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCurrencyEndpoints:
    """Test currency conversion endpoints."""

    @pytest.mark.asyncio
    async def test_get_currency_rate(self, client, auth_headers):
        """Test getting currency rate."""
        response = await client.get(
            "/v1/currency/rate?from_currency=USD&to_currency=RUB",
            headers=auth_headers
        )
        # May fail if external API is down
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "rate" in data
            assert data["from_currency"] == "USD"
            assert data["to_currency"] == "RUB"

    @pytest.mark.asyncio
    async def test_convert_currency_preview(self, client, auth_headers, test_user):
        """Test currency conversion preview."""
        # Skip if user already has RUB
        if test_user.currency == "RUB":
            pytest.skip("User already has RUB currency")
            
        response = await client.post(
            "/v1/currency/convert?new_currency=RUB",
            headers=auth_headers
        )
        # May fail if external API is down
        assert response.status_code in [200, 400, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "rate" in data
            assert "preview" in data
            assert "current_income" in data["preview"]
            assert "new_income" in data["preview"]

    @pytest.mark.asyncio
    async def test_convert_currency_same_currency(self, client, auth_headers, test_user):
        """Test that converting to same currency returns error."""
        response = await client.post(
            f"/v1/currency/convert?new_currency={test_user.currency}",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already using" in response.json()["detail"].lower()


class TestStatsEndpoints:
    """Test statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, client, auth_headers):
        """Test getting dashboard stats."""
        response = await client.get("/v1/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "balance" in data
        assert "by_category" in data
        assert "recent_transactions" in data

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_with_period(self, client, auth_headers):
        """Test getting dashboard stats with period filter."""
        for period in ["month", "year", "all"]:
            response = await client.get(
                f"/v1/stats/dashboard?period={period}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "total_income" in data


class TestValidationErrors:
    """Test that validation errors are handled properly."""

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_amount(self, client, auth_headers):
        """Test creating transaction with invalid amount."""
        response = await client.post("/v1/transactions", headers=auth_headers, json={
            "type": "expense",
            "amount": -50,  # Negative amount
            "category_name": "Test",
            "transaction_date": datetime.now().isoformat()
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_transaction_missing_required(self, client, auth_headers):
        """Test creating transaction without required fields."""
        response = await client.post("/v1/transactions", headers=auth_headers, json={
            "type": "expense"
            # Missing amount, category_name, transaction_date
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        """Test registration with too short password."""
        response = await client.post("/v1/auth/register", json={
            "username": "newuser",
            "password": "123"  # Too short
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_long_password(self, client):
        """Test registration with password > 71 chars."""
        response = await client.post("/v1/auth/register", json={
            "username": "newuser",
            "password": "a" * 100  # Too long for bcrypt
        })
        assert response.status_code == 422
