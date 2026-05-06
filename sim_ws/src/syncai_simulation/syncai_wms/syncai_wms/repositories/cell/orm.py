from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Float, Index, String, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from syncai_wms.repositories.cell.schema import FunctionTypeCategory


class Base(DeclarativeBase):
    pass


class CellORM(Base):
    __tablename__ = "cells"
    __table_args__ = (
        Index(
            "uq_cells_map_display_name_active",
            "map_id",
            "display_name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_cells_map_id", "map_id"),
        Index("ix_cells_area_id", "area_id"),
        Index("ix_cells_function_type_category", "function_type_category"),
    )

    uuid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    map_id: Mapped[str] = mapped_column(String(64), nullable=False)
    area_id: Mapped[str] = mapped_column(String(64), nullable=False)
    cell_position_x: Mapped[float] = mapped_column(Float, nullable=False)
    cell_position_y: Mapped[float] = mapped_column(Float, nullable=False)
    cell_orientation_r: Mapped[float] = mapped_column(
        Float, nullable=False, server_default=text("0")
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    function_type_category: Mapped[FunctionTypeCategory] = mapped_column(
        String(32), nullable=False
    )
    function_type_name: Mapped[str] = mapped_column(String(64), nullable=False)
    occupied_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
