from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from syncai_wms.repositories.cell.cell import (
    CellNotFoundError,
    CellRepo,
    DuplicateDisplayNameError,
)
from syncai_wms.repositories.cell.schema import (
    CellCreate,
    CellListResponse,
    CellResponse,
    CellUpdate,
    FunctionTypeCategory,
)


def init_cell_router(cell_repo: CellRepo) -> APIRouter:
    router = APIRouter(prefix="/api/v1/wms/cells", tags=["cells"])

    @router.post(
        "",
        response_model=CellResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_cell(payload: CellCreate) -> CellResponse:
        try:
            return await cell_repo.create(payload)
        except DuplicateDisplayNameError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"display_name already exists: {exc}",
            )

    @router.get("", response_model=CellListResponse)
    async def list_cells(
        map_id: Optional[str] = Query(default=None),
        area_id: Optional[str] = Query(default=None),
        function_type_category: Optional[FunctionTypeCategory] = Query(default=None),
        occupied: Optional[bool] = Query(default=None),
        include_deleted: bool = Query(default=False),
    ) -> CellListResponse:
        cells = await cell_repo.list(
            map_id=map_id,
            area_id=area_id,
            function_type_category=function_type_category,
            occupied=occupied,
            include_deleted=include_deleted,
        )
        return CellListResponse(cells=cells)

    @router.get("/{cell_uuid}", response_model=CellResponse)
    async def get_cell(
        cell_uuid: UUID,
        include_deleted: bool = Query(default=False),
    ) -> CellResponse:
        try:
            return await cell_repo.get_by_id(cell_uuid, include_deleted=include_deleted)
        except CellNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"cell not found: {cell_uuid}",
            )

    @router.patch("/{cell_uuid}", response_model=CellResponse)
    async def update_cell(cell_uuid: UUID, payload: CellUpdate) -> CellResponse:
        try:
            return await cell_repo.update(cell_uuid, payload)
        except CellNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"cell not found: {cell_uuid}",
            )
        except DuplicateDisplayNameError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"display_name already exists: {exc}",
            )

    @router.delete("/{cell_uuid}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_cell(cell_uuid: UUID) -> Response:
        try:
            await cell_repo.soft_delete(cell_uuid)
        except CellNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"cell not found: {cell_uuid}",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
