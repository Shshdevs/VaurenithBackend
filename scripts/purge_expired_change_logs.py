import asyncio
from datetime import UTC, datetime, timedelta

from app.infrastructure.persistence.database import SessionLocal, engine
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)


async def main() -> None:
    async with SessionLocal() as session, session.begin():
        deleted_count = await SqlAlchemyChangeLogRepository(session).purge_expired(
            datetime.now(UTC) - timedelta(days=365)
        )
    print(f"Deleted {deleted_count} expired ChangeLog entries")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
