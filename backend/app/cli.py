"""CLI commands for administrative tasks."""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import Base


async def create_admin(username: str, password: str):
    """Create an admin user."""
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=type('AsyncSession', (), {}))
    
    async with AsyncSessionLocal() as session:
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


async def list_users():
    """List all users."""
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, class_=type('AsyncSession', (), {}))
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"{'ID':<5} {'Username':<20} {'Admin':<6} {'Active':<7} {'Deleted':<8}")
        print("-" * 60)
        for user in users:
            deleted = "Yes" if user.deleted_at else "No"
            print(f"{user.id:<5} {user.username:<20} {'Yes' if user.is_admin else 'No':<6} {'Yes' if user.is_active else 'No':<7} {deleted:<8}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command> [args]")
        print("Commands:")
        print("  create-admin <username> <password>  - Create admin user")
        print("  list-users                          - List all users")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create-admin":
        if len(sys.argv) != 4:
            print("Usage: python -m app.cli create-admin <username> <password>")
            sys.exit(1)
        asyncio.run(create_admin(sys.argv[2], sys.argv[3]))
    elif command == "list-users":
        asyncio.run(list_users())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
