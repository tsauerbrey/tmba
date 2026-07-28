import base64

from tmba.services.shairport_metadata import parse_metadata_item


def item(item_type: str, code: str, text: str = "") -> bytes:
    data = base64.b64encode(text.encode()).decode()
    return (
        f"<item><type>{item_type}</type><code>{code}</code>"
        f"<length>{len(text.encode())}</length><data>{data}</data></item>"
    ).encode()


def test_parse_title():
    parsed = parse_metadata_item(item("core", "minm", "Hotel California"))
    assert parsed is not None
    assert parsed.item_type == "core"
    assert parsed.code == "minm"
    assert parsed.text == "Hotel California"


def test_parse_empty_event():
    parsed = parse_metadata_item(item("ssnc", "pbeg"))
    assert parsed is not None
    assert parsed.payload == b""
