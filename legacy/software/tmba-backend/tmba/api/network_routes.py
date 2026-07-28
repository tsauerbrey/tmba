"""HTTP routes for TMBA network diagnostics and Wi-Fi management."""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from tmba.services.network_service import network_service


router = APIRouter(
    prefix="/network",
    tags=["Network"],
)


class WifiConnectRequest(BaseModel):
    ssid: str = Field(min_length=1, max_length=64)
    password: str | None = Field(
        default=None,
        max_length=128,
    )
    hidden: bool = False


class WifiDisconnectRequest(BaseModel):
    interface: str | None = Field(
        default=None,
        max_length=32,
    )


class WifiForgetRequest(BaseModel):
    connection: str = Field(min_length=1, max_length=128)


@router.get("/status")
def get_network_status():
    return network_service.get_status()


@router.get("/interfaces")
def get_network_interfaces():
    return network_service.get_interfaces()


@router.get("/wifi/scan")
def scan_wifi_networks():
    return network_service.scan_wifi()


@router.get("/wifi/saved")
def get_saved_wifi_connections():
    return network_service.get_saved_wifi()


@router.post("/wifi/connect")
def connect_wifi(request: WifiConnectRequest):
    return network_service.connect_wifi(
        ssid=request.ssid,
        password=request.password,
        hidden=request.hidden,
    )


@router.post("/wifi/disconnect")
def disconnect_wifi(request: WifiDisconnectRequest):
    return network_service.disconnect_wifi(
        interface=request.interface,
    )


@router.post("/wifi/forget")
def forget_wifi(request: WifiForgetRequest):
    return network_service.forget_wifi(
        connection=request.connection,
    )
