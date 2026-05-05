import structlog
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from syncai_wms.db.session import get_admin_db_url, get_target_db_name
from syncai_wms.repositories.cell.orm import Base


async def ensure_database_exists(
    logger: structlog.stdlib.BoundLogger,
) -> None:
    """Connect to the system `postgres` DB and create the target DB if missing.

    Uses AUTOCOMMIT because CREATE DATABASE cannot run inside a transaction.
    """
    target = get_target_db_name()
    admin_url = get_admin_db_url()
    admin_engine: AsyncEngine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", future=True
    )
    try:
        async with admin_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target},
            )
            exists = result.scalar() is not None
            if exists:
                logger.info("[Bootstrap] database exists", db=target)
                return
            if not target.replace("_", "").isalnum():
                raise ValueError(f"Unsafe database name: {target!r}")
            await conn.execute(text(f'CREATE DATABASE "{target}"'))
            logger.info("[Bootstrap] database created", db=target)
    except ProgrammingError as exc:
        logger.warning("[Bootstrap] CREATE DATABASE skipped", error=str(exc))
    finally:
        await admin_engine.dispose()


async def create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def bootstrap(
    logger: structlog.stdlib.BoundLogger,
    engine: AsyncEngine,
) -> None:
    """Idempotent startup routine: create tables only.

    Cells are populated via the REST API; no auto-seed is performed.
    """
    await create_tables(engine)
    logger.info("[Bootstrap] tables ready")
