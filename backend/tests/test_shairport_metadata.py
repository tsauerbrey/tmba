import base64
from pathlib import Path

from tmba.services.shairport_metadata import (
    AirPlayArtworkStore,
    ShairportMetadataObserver,
    parse_metadata_item,
)


def item(
    item_type: str,
    code: str,
    payload: bytes = b"",
) -> bytes:
    data = base64.b64encode(payload).decode()
    return (
        f"<item><type>{item_type}</type><code>{code}</code>"
        f"<length>{len(payload)}</length><data>{data}</data></item>"
    ).encode()


def test_parse_title():
    parsed = parse_metadata_item(
        item("core", "minm", b"Hotel California")
    )
    assert parsed is not None
    assert parsed.item_type == "core"
    assert parsed.code == "minm"
    assert parsed.text == "Hotel California"


def test_parse_hex_fourcc():
    parsed = parse_metadata_item(
        item("73736e63", "50494354", b"\xff\xd8\xffcover")
    )
    assert parsed is not None
    assert parsed.item_type == "ssnc"
    assert parsed.code == "PICT"


def test_artwork_store_writes_atomically(tmp_path: Path):
    target = tmp_path / "current.jpg"
    store = AirPlayArtworkStore(target)
    payload = b"\xff\xd8\xff" + b"jpeg-data"

    assert store.store(payload) is True
    assert target.read_bytes() == payload
    assert not (tmp_path / ".current.jpg.tmp").exists()


def test_artwork_store_skips_duplicate(tmp_path: Path):
    target = tmp_path / "current.jpg"
    store = AirPlayArtworkStore(target)
    payload = b"\xff\xd8\xff" + b"same-cover"

    assert store.store(payload) is True
    first_mtime = target.stat().st_mtime_ns
    assert store.store(payload) is False
    assert target.stat().st_mtime_ns == first_mtime


def test_observer_accepts_pict_and_hex_pict(tmp_path: Path):
    target = tmp_path / "current.jpg"
    observer = ShairportMetadataObserver(
        fifo_path=tmp_path / "fifo",
        artwork_store=AirPlayArtworkStore(target),
    )
    first = b"\xff\xd8\xff" + b"first"
    second = b"\x89PNG\r\n\x1a\n" + b"second"

    observer.feed(item("ssnc", "PICT", first))
    assert target.read_bytes() == first

    observer.feed(item("73736e63", "50494354", second))
    assert target.read_bytes() == second


def test_new_title_removes_stale_cover(tmp_path: Path):
    target = tmp_path / "current.jpg"
    store = AirPlayArtworkStore(target)
    observer = ShairportMetadataObserver(
        fifo_path=tmp_path / "fifo",
        artwork_store=store,
    )

    observer.feed(item("ssnc", "PICT", b"\xff\xd8\xffold"))
    assert target.exists()

    observer.feed(item("core", "minm", b"New title"))
    assert not target.exists()
