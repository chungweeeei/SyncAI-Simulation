import os
from typing import Tuple
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DEFAULT_DB_NAME = "syncai_wms"
DEFAULT_DB_HOST = "postgresql"
DEFAULT_DB_PORT = "5432"


def _build_default_url(db_name: str = DEFAULT_DB_NAME) -> str:
    user = quote_plus(os.getenv("POSTGRES_USER", "admin"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", "admin"))
    host = os.getenv("SYNCAI_WMS_DB_HOST", DEFAULT_DB_HOST)
    port = os.getenv("SYNCAI_WMS_DB_PORT", DEFAULT_DB_PORT)
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


def get_db_url() -> str:
    return os.getenv("SYNCAI_WMS_DB_URL") or _build_default_url()


def get_admin_db_url() -> str:
    """URL to the system `postgres` DB used for `CREATE DATABASE`."""
    return _build_default_url(db_name="postgres")


def get_target_db_name() -> str:
    explicit = os.getenv("SYNCAI_WMS_DB_URL")
    if explicit:
        # parse path component after last '/'
        return explicit.rsplit("/", 1)[-1].split("?", 1)[0] or DEFAULT_DB_NAME
    return DEFAULT_DB_NAME


def create_engine_and_factory(
    url: str,
) -> Tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, factory
