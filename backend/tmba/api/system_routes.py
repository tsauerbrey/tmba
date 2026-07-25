"""HTTP routes for TMBA system information and diagnostics."""

from fastapi import APIRouter

from tmba.services.system_service import system_service


router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
def get_system_health():
    return system_service.get_health()


@router.get("/info")
def get_system_info():
    return system_service.get_info()
