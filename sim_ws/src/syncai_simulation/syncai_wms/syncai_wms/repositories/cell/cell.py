from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from syncai_wms.repositories.cell.orm import CellORM
from syncai_wms.repositories.cell.schema import (
    CellCreate,
    CellResponse,
    CellUpdate,
    FunctionTypeCategory,
)


class DuplicateDisplayNameError(Exception):
    pass


class CellNotFoundError(Exception):
    pass


class CellRepo:

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    ):
        self._logger = logger
        self._session_factory = session_factory

    def bind_session_factory(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    def _factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError(
                "CellRepo session factory not bound; bootstrap did not complete."
            )
        return self._session_factory

    async def create(self, payload: CellCreate) -> CellResponse:
        async with self._factory()() as session:
            row = CellORM(**payload.model_dump())
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise DuplicateDisplayNameError(payload.display_name) from exc
            await session.refresh(row)
            return CellResponse.model_validate(row, from_attributes=True)

    async def list(
        self,
        map_id: Optional[str] = None,
        area_id: Optional[str] = None,
        function_type_category: Optional[FunctionTypeCategory] = None,
        occupied: Optional[bool] = None,
        include_deleted: bool = False,
    ) -> List[CellResponse]:
        async with self._factory()() as session:
            stmt = select(CellORM)

            if not include_deleted:
                stmt = stmt.where(CellORM.deleted_at.is_(None))

            if map_id is not None:
                stmt = stmt.where(CellORM.map_id == map_id)

            if area_id is not None:
                stmt = stmt.where(CellORM.area_id == area_id)

            if function_type_category is not None:
                stmt = stmt.where(
                    CellORM.function_type_category == function_type_category
                )

            if occupied is True:
                stmt = stmt.where(CellORM.occupied_by.is_not(None))
            elif occupied is False:
                stmt = stmt.where(CellORM.occupied_by.is_(None))

            stmt = stmt.order_by(CellORM.created_at.asc())

            rows = (await session.execute(stmt)).scalars().all()
            return [
                CellResponse.model_validate(row, from_attributes=True) for row in rows
            ]

    async def get_by_id(
        self, cell_uuid: UUID, include_deleted: bool = False
    ) -> CellResponse:
        async with self._factory()() as session:
            row = await self._fetch(session, cell_uuid, include_deleted)
            return CellResponse.model_validate(row, from_attributes=True)

    async def update(self, cell_uuid: UUID, payload: CellUpdate) -> CellResponse:
        data = payload.model_dump(exclude_unset=True)
        async with self._factory()() as session:
            row = await self._fetch(session, cell_uuid, include_deleted=False)
            for key, value in data.items():
                setattr(row, key, value)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise DuplicateDisplayNameError(
                    data.get("display_name", row.display_name)
                ) from exc
            await session.refresh(row)
            return CellResponse.model_validate(row, from_attributes=True)

    async def soft_delete(self, cell_uuid: UUID) -> None:
        async with self._factory()() as session:
            row = await self._fetch(session, cell_uuid, include_deleted=False)
            row.deleted_at = datetime.now(timezone.utc)
            await session.commit()

    async def _fetch(
        self, session: AsyncSession, cell_uuid: UUID, include_deleted: bool
    ) -> CellORM:
        stmt = select(CellORM).where(CellORM.uuid == cell_uuid)
        if not include_deleted:
            stmt = stmt.where(CellORM.deleted_at.is_(None))
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise CellNotFoundError(str(cell_uuid))
        return row


def init_cell_repo(logger: structlog.stdlib.BoundLogger) -> CellRepo:
    return CellRepo(logger=logger)
