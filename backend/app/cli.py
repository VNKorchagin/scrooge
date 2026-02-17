"""CLI commands for administrative tasks."""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command> [args]")
        print("Commands:")
        print("  create-admin <username> <password>  - Create admin user")
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
