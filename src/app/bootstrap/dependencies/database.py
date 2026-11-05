from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.persistence.database import SessionLocal


async def get_database_session() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
