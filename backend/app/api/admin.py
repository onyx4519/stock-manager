from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth import get_current_admin
from app.dependencies import admin_repository as repository
from app.schemas.admin import AdminDashboardSummary
from app.schemas.auth import AuthUser


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardSummary)
def dashboard(
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> AdminDashboardSummary:
    return repository.get_dashboard_summary()
