import pytest

from tmba.audio.engine_state import EngineSource
from tmba.audio.source_arbitration import (
    ArbitrationAction,
    SourceArbitrator,
)


def test_default_priority_order():
    arbitrator = SourceArbitrator()
    assert arbitrator.priority("airplay") > arbitrator.priority("bluetooth")
    assert arbitrator.priority("bluetooth") > arbitrator.priority("webradio")
    assert arbitrator.priority("webradio") > arbitrator.priority("none")


def test_higher_priority_source_may_interrupt():
    decision = SourceArbitrator().decide("webradio", "bluetooth")
    assert decision.accepted is True
    assert decision.action is ArbitrationAction.ACTIVATE


def test_lower_priority_source_is_rejected():
    decision = SourceArbitrator().decide("airplay", "webradio")
    assert decision.accepted is False
    assert decision.action is ArbitrationAction.REJECT


def test_force_bypasses_priority():
    decision = SourceArbitrator().decide(
        "airplay", "webradio", force=True
    )
    assert decision.accepted is True
    assert decision.forced is True


def test_none_always_deactivates():
    decision = SourceArbitrator().decide("airplay", EngineSource.NONE)
    assert decision.accepted is True
    assert decision.action is ArbitrationAction.DEACTIVATE


def test_same_source_is_kept_without_switch():
    decision = SourceArbitrator().decide("bluetooth", "bluetooth")
    assert decision.accepted is True
    assert decision.action is ArbitrationAction.KEEP_CURRENT


def test_priorities_can_be_overridden():
    arbitrator = SourceArbitrator({"webradio": 99})
    decision = arbitrator.decide("airplay", "webradio")
    assert decision.accepted is True


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError, match="Unbekannte Audioquelle"):
        SourceArbitrator().priority("cassette")
