from unittest.mock import patch

from tmba.services.network_service import NetworkService


def test_network_status_contains_required_fields():
    service = NetworkService()

    status = service.get_status()

    assert isinstance(status["connected"], bool)
    assert status["hostname"]
    assert status["platform"]
    assert status["backend"]
    assert isinstance(status["active_interfaces"], list)
    assert "wifi" in status


def test_network_interfaces_contains_list():
    service = NetworkService()

    result = service.get_interfaces()

    assert result["count"] >= 1
    assert isinstance(result["interfaces"], list)

    first = result["interfaces"][0]
    assert first["name"]
    assert isinstance(first["is_up"], bool)
    assert isinstance(first["addresses"], list)


def test_wifi_scan_has_stable_response_shape():
    service = NetworkService()

    result = service.scan_wifi()

    assert isinstance(result["supported"], bool)
    assert result["backend"]
    assert isinstance(result["networks"], list)


@patch.object(NetworkService, "_detect_backend", return_value="macos")
def test_connect_is_safe_on_macos(_mock_backend):
    service = NetworkService()

    result = service.connect_wifi(
        ssid="Testnetz",
        password="geheim",
    )

    assert result["supported"] is False
    assert result["success"] is False
    assert result["ssid"] == "Testnetz"
    assert "password" not in result
    assert "geheim" not in str(result)


@patch.object(NetworkService, "_detect_backend", return_value="macos")
def test_disconnect_is_safe_on_macos(_mock_backend):
    service = NetworkService()

    result = service.disconnect_wifi()

    assert result["supported"] is False
    assert result["success"] is False


@patch.object(NetworkService, "_detect_backend", return_value="macos")
def test_saved_connections_are_safe_on_macos(_mock_backend):
    service = NetworkService()

    result = service.get_saved_wifi()

    assert result["supported"] is False
    assert result["connections"] == []


@patch.object(NetworkService, "_detect_backend", return_value="macos")
def test_forget_is_safe_on_macos(_mock_backend):
    service = NetworkService()

    result = service.forget_wifi("Testnetz")

    assert result["supported"] is False
    assert result["success"] is False
