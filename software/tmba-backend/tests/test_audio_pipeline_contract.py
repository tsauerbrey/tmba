from __future__ import annotations

from fastapi.testclient import TestClient

from tmba.main import app


client = TestClient(app)

VALID_PIPELINE_STATES = {
    "created",
    "ready",
    "running",
    "stopped",
    "error",
}

EXPECTED_STAGE_ORDER = [
    "source_gain",
    "replay_gain",
    "loudness",
    "equalizer",
    "limiter",
    "output",
]


def get_pipeline_payload() -> dict:
    response = client.get("/audio/pipeline")

    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)

    return payload


def test_pipeline_contract_has_stable_top_level_fields() -> None:
    payload = get_pipeline_payload()

    assert set(payload) == {
        "state",
        "stage_count",
        "enabled_stage_count",
        "output",
        "stages",
        "config",
    }


def test_pipeline_contract_uses_expected_stage_order() -> None:
    payload = get_pipeline_payload()

    stage_names = [
        stage["name"]
        for stage in payload["stages"]
    ]

    assert stage_names == EXPECTED_STAGE_ORDER
    assert payload["stage_count"] == len(EXPECTED_STAGE_ORDER)


def test_pipeline_contract_counts_enabled_stages_correctly() -> None:
    payload = get_pipeline_payload()

    enabled_count = sum(
        bool(stage["enabled"])
        for stage in payload["stages"]
    )

    assert payload["enabled_stage_count"] == enabled_count


def test_pipeline_contract_has_exactly_one_final_output_stage() -> None:
    payload = get_pipeline_payload()
    output_stages = [
        stage
        for stage in payload["stages"]
        if stage["stage_type"] == "output"
    ]

    assert len(output_stages) == 1
    assert payload["stages"][-1]["stage_type"] == "output"


def test_pipeline_contract_exposes_output_format() -> None:
    payload = get_pipeline_payload()
    output = payload["output"]

    assert output["driver"]
    assert output["device"]
    assert isinstance(output["sample_rate"], int)
    assert output["sample_rate"] > 0
    assert isinstance(output["channels"], int)
    assert output["channels"] > 0
    assert output["format"]


def test_pipeline_contract_state_is_valid() -> None:
    payload = get_pipeline_payload()

    assert payload["state"] in VALID_PIPELINE_STATES


def test_openapi_documents_pipeline_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    document = response.json()
    endpoint = document["paths"]["/audio/pipeline"]["get"]

    assert "Audio" in endpoint["tags"]
    assert endpoint["responses"]["200"]
