from __future__ import annotations

import time

import pytest

from tmba.audio.sources import DummySource, SourceLifecycleState


def wait_until(predicate, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("Bedingung wurde nicht rechtzeitig erfüllt.")


def test_dummy_source_connect_start_and_stop():
    blocks: list[bytes] = []

    def writer(data: bytes) -> int:
        blocks.append(data)
        return len(data)

    source = DummySource(writer, frames_per_block=48)
    assert source.connect().state is SourceLifecycleState.READY
    assert source.start().state is SourceLifecycleState.PLAYING
    wait_until(lambda: len(blocks) >= 2)
    stopped = source.stop()

    assert stopped.state is SourceLifecycleState.READY
    assert stopped.active is False
    assert stopped.details["thread_alive"] is False
    assert stopped.details["blocks_written"] >= 2
    assert stopped.details["bytes_written"] == sum(map(len, blocks))


def test_dummy_source_pause_and_resume():
    calls = 0

    def writer(data: bytes) -> int:
        nonlocal calls
        calls += 1
        return len(data)

    source = DummySource(writer, frames_per_block=48)
    source.start()
    wait_until(lambda: calls >= 2)
    assert source.pause().state is SourceLifecycleState.PAUSED
    paused_calls = calls
    time.sleep(0.03)
    assert calls <= paused_calls + 1
    assert source.resume().state is SourceLifecycleState.PLAYING
    wait_until(lambda: calls > paused_calls + 1)
    source.stop()


def test_disconnect_stops_thread_and_releases_source():
    source = DummySource(lambda data: len(data), frames_per_block=48)
    source.start()
    wait_until(lambda: source.status().details["blocks_written"] >= 1)
    status = source.disconnect()
    assert status.state is SourceLifecycleState.DISCONNECTED
    assert status.connected is False
    assert status.active is False
    assert status.details["thread_alive"] is False


def test_writer_error_moves_source_to_error_state():
    def writer(_data: bytes) -> int:
        raise OSError("Ausgabe nicht verfügbar")

    source = DummySource(writer, frames_per_block=48)
    source.start()
    wait_until(lambda: source.status().state is SourceLifecycleState.ERROR)
    status = source.status()
    assert status.active is False
    assert "nicht verfügbar" in str(status.error)
    source.stop()


def test_pause_before_start_is_rejected():
    source = DummySource(lambda data: len(data))
    with pytest.raises(RuntimeError, match="spielt derzeit nicht"):
        source.pause()
