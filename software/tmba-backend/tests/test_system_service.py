from tmba.services.system_service import SystemService


def test_system_info_contains_required_sections():
    service = SystemService()

    info = service.get_info()

    assert info["project"] == "TMBA"
    assert info["version"]
    assert info["hostname"]
    assert info["platform"]["system"]
    assert info["cpu"]["logical_cores"] >= 1
    assert info["memory"]["total_bytes"] > 0
    assert info["disk"]["total_bytes"] > 0
    assert info["uptime"]["system_seconds"] >= 0
    assert info["uptime"]["backend_seconds"] >= 0


def test_system_health_is_ok():
    service = SystemService()

    health = service.get_health()

    assert health["status"] == "ok"
    assert health["project"] == "TMBA"
    assert health["version"]
    assert health["timestamp"]
