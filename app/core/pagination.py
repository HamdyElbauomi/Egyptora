"""Shared pagination for list endpoints.

Every paginated endpoint takes ?page=1&limit=20 and returns:
    {"data": [...], "page": 1, "limit": 20, "total": 57}
"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    data: list[T]
    page: int
    limit: int
    total: int


class PageParams:
    """Use as a dependency: `params: PageParams = Depends()`."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number, starting at 1"),
        limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    ):
        self.page = page
        self.limit = limit

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def paginate(db: Session, stmt: Select, params: PageParams) -> tuple[list, int]:
    """Runs `stmt` for one page and counts all matching rows. Returns (rows, total)."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = list(db.scalars(stmt.offset(params.offset).limit(params.limit)))
    return rows, int(total or 0)
