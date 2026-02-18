"""CLI commands for administrative tasks."""
import asyncio
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType, TransactionSource
from app.core.database import Base


async def create_admin(username: str, password: str):
    """Create an admin user."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        
        if existing:
            # Make existing user admin
            existing.is_admin = True
            await session.commit()
            print(f"User '{username}' is now an admin")
        else:
            # Create new admin user
            user = User(
                username=username,
                hashed_password=get_password_hash(password),
                is_admin=True,
                is_active=True
            )
            session.add(user)
            await session.commit()
            print(f"Admin user '{username}' created successfully")
    
    await engine.dispose()


async def list_users():
    """List all users."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"{'ID':<5} {'Username':<20} {'Admin':<6} {'Active':<7} {'Deleted':<8}")
        print("-" * 60)
        for user in users:
            deleted = "Yes" if user.deleted_at else "No"
            print(f"{user.id:<5} {user.username:<20} {'Yes' if user.is_admin else 'No':<6} {'Yes' if user.is_active else 'No':<7} {deleted:<8}")
    
    await engine.dispose()


async def delete_user(username: str, hard: bool = False):
    """Delete a user (soft or hard delete)."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        from datetime import datetime
        
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User '{username}' not found")
            await engine.dispose()
            return
        
        if hard:
            # Permanent deletion
            await session.delete(user)
            await session.commit()
            print(f"User '{username}' permanently deleted (hard delete)")
        else:
            # Soft delete
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            await session.commit()
            print(f"User '{username}' soft deleted (can be restored)")
    
    await engine.dispose()


async def restore_user(username: str):
    """Restore a soft-deleted user."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User '{username}' not found")
            await engine.dispose()
            return
        
        if user.is_active:
            print(f"User '{username}' is already active")
            await engine.dispose()
            return
        
        user.is_active = True
        user.deleted_at = None
        await session.commit()
        print(f"User '{username}' restored successfully")
    
    await engine.dispose()


async def create_demo_user(username: str = "demo", password: str = "demo123"):
    """Create a demo user with sample data for testing."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from sqlalchemy import select
        
        # Check if user exists
        result = await session.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"User '{username}' already exists. Delete it first to recreate demo data.")
            await engine.dispose()
            return
        
        # Create demo user
        user = User(
            username=username,
            hashed_password=get_password_hash(password),
            is_admin=False,
            is_active=True,
            language="en",
            currency="USD"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Demo user '{username}' created with password '{password}'")
        
        # Create income categories
        income_categories = ["Salary", "Freelance", "Investments", "Gifts", "Other Income"]
        income_cats = []
        for cat_name in income_categories:
            cat = Category(name=cat_name, user_id=user.id)
            session.add(cat)
            income_cats.append(cat)
        await session.commit()
        
        # Create expense categories
        expense_categories = [
            "Food & Groceries",
            "Transport",
            "Housing",
            "Utilities",
            "Entertainment",
            "Healthcare",
            "Shopping",
            "Education",
            "Travel",
            "Subscriptions"
        ]
        expense_cats = []
        for cat_name in expense_categories:
            cat = Category(name=cat_name, user_id=user.id)
            session.add(cat)
            expense_cats.append(cat)
        await session.commit()
        
        # Refresh categories to get IDs
        for cat in income_cats + expense_cats:
            await session.refresh(cat)
        
        print(f"Created {len(income_categories)} income and {len(expense_categories)} expense categories")
        
        # Generate transactions for the last 6 months
        now = datetime.utcnow()
        transactions = []
        
        # Income transactions (monthly salary + occasional freelance)
        for month_offset in range(6, -1, -1):
            month_date = now - timedelta(days=month_offset * 30)
            
            # Monthly salary
            salary_date = month_date.replace(day=random.randint(1, 5))
            transactions.append(Transaction(
                user_id=user.id,
                type=TransactionType.INCOME,
                amount=Decimal("5000.00"),
                category_id=income_cats[0].id,  # Salary
                category_name=income_cats[0].name,
                description="Monthly salary",
                transaction_date=salary_date,
                source=TransactionSource.MANUAL
            ))
            
            # Occasional freelance (not every month)
            if random.random() > 0.3:
                freelance_date = month_date.replace(day=random.randint(10, 25))
                transactions.append(Transaction(
                    user_id=user.id,
                    type=TransactionType.INCOME,
                    amount=Decimal(str(random.randint(500, 2000))),
                    category_id=income_cats[1].id,  # Freelance
                    category_name=income_cats[1].name,
                    description="Freelance project",
                    transaction_date=freelance_date,
                    source=TransactionSource.MANUAL
                ))
        
        # Expense transactions
        expense_templates = [
            ("Weekly groceries", 80, 150, expense_cats[0]),  # Food
            ("Restaurant", 30, 80, expense_cats[0]),  # Food
            ("Gas", 40, 70, expense_cats[1]),  # Transport
            ("Public transport", 20, 50, expense_cats[1]),  # Transport
            ("Rent", 1200, 1200, expense_cats[2]),  # Housing
            ("Electricity", 80, 120, expense_cats[3]),  # Utilities
            ("Internet", 50, 50, expense_cats[3]),  # Utilities
            ("Movie night", 20, 40, expense_cats[4]),  # Entertainment
            ("Game purchase", 30, 60, expense_cats[4]),  # Entertainment
            ("Pharmacy", 15, 50, expense_cats[5]),  # Healthcare
            ("Doctor visit", 50, 150, expense_cats[5]),  # Healthcare
            ("Clothing", 50, 200, expense_cats[6]),  # Shopping
            ("Online course", 30, 100, expense_cats[7]),  # Education
            ("Flight tickets", 200, 500, expense_cats[8]),  # Travel
            ("Hotel", 100, 300, expense_cats[8]),  # Travel
            ("Netflix", 15, 15, expense_cats[9]),  # Subscriptions
            ("Spotify", 10, 10, expense_cats[9]),  # Subscriptions
        ]
        
        # Generate ~80 expense transactions over 6 months
        for _ in range(80):
            template = random.choice(expense_templates)
            name, min_amount, max_amount, category = template
            
            # Random date within last 6 months
            days_ago = random.randint(0, 180)
            trans_date = now - timedelta(days=days_ago)
            
            amount = Decimal(str(round(random.uniform(min_amount, max_amount), 2)))
            
            transactions.append(Transaction(
                user_id=user.id,
                type=TransactionType.EXPENSE,
                amount=amount,
                category_id=category.id,
                category_name=category.name,
                description=name,
                transaction_date=trans_date,
                source=TransactionSource.MANUAL
            ))
        
        # Add all transactions
        for trans in transactions:
            session.add(trans)
        
        await session.commit()
        
        # Count totals
        income_count = len([t for t in transactions if t.type == TransactionType.INCOME])
        expense_count = len([t for t in transactions if t.type == TransactionType.EXPENSE])
        total_income = sum([t.amount for t in transactions if t.type == TransactionType.INCOME])
        total_expense = sum([t.amount for t in transactions if t.type == TransactionType.EXPENSE])
        
        print(f"Created {income_count} income transactions (total: ${total_income})")
        print(f"Created {expense_count} expense transactions (total: ${total_expense})")
        print(f"\nDemo user is ready! Login with:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
    
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command> [args]")
        print("Commands:")
        print("  create-admin <username> <password>  - Create admin user")
        print("  create-demo [username] [password]   - Create demo user with sample data")
        print("  list-users                          - List all users")
        print("  delete-user <username> [--hard]     - Soft delete user (use --hard for permanent)")
        print("  restore-user <username>             - Restore soft-deleted user")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create-admin":
        if len(sys.argv) != 4:
            print("Usage: python -m app.cli create-admin <username> <password>")
            sys.exit(1)
        asyncio.run(create_admin(sys.argv[2], sys.argv[3]))
    elif command == "create-demo":
        username = sys.argv[2] if len(sys.argv) > 2 else "demo"
        password = sys.argv[3] if len(sys.argv) > 3 else "demo123"
        asyncio.run(create_demo_user(username, password))
    elif command == "list-users":
        asyncio.run(list_users())
    elif command == "delete-user":
        if len(sys.argv) < 3:
            print("Usage: python -m app.cli delete-user <username> [--hard]")
            sys.exit(1)
        username = sys.argv[2]
        hard = "--hard" in sys.argv
        asyncio.run(delete_user(username, hard))
    elif command == "restore-user":
        if len(sys.argv) != 3:
            print("Usage: python -m app.cli restore-user <username>")
            sys.exit(1)
        asyncio.run(restore_user(sys.argv[2]))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
