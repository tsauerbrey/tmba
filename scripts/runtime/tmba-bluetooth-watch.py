#!/usr/bin/env python3

import json
import subprocess
import time
import urllib.error
import urllib.request

API_BASE = "http://127.0.0.1:8000"
POLL_INTERVAL = 2.0


def run_command(*args: str) -> str:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def get_connected_device() -> tuple[bool, str]:
    devices_output = run_command(
        "bluetoothctl",
        "devices",
        "Connected",
    )

    for line in devices_output.splitlines():
        parts = line.strip().split(maxsplit=2)

        if len(parts) < 2 or parts[0] != "Device":
            continue

        address = parts[1]
        fallback_name = parts[2] if len(parts) >= 3 else "Bluetooth-Gerät"

        info_output = run_command(
            "bluetoothctl",
            "info",
            address,
        )

        connected = False
        device_name = fallback_name

        for info_line in info_output.splitlines():
            stripped = info_line.strip()

            if stripped.startswith("Connected:"):
                connected = stripped.split(":", 1)[1].strip().lower() == "yes"

            elif stripped.startswith("Name:"):
                device_name = stripped.split(":", 1)[1].strip() or fallback_name

            elif stripped.startswith("Alias:") and device_name == fallback_name:
                device_name = stripped.split(":", 1)[1].strip() or fallback_name

        if connected:
            return True, device_name

    return False, ""


def post(path: str, payload: dict | None = None) -> None:
    data = None
    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        API_BASE + path,
        data=data,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=3) as response:
        response.read()


def main() -> None:
    previous_connected: bool | None = None
    previous_device_name = ""

    while True:
        connected, device_name = get_connected_device()

        state_changed = (
            connected != previous_connected
            or (
                connected
                and device_name != previous_device_name
            )
        )

        if state_changed:
            try:
                if connected:
                    post("/bluetooth/session/start")
                    print(
                        f"Bluetooth verbunden: {device_name}",
                        flush=True,
                    )
                else:
                    post("/bluetooth/session/end")
                    print(
                        "Bluetooth getrennt",
                        flush=True,
                    )

                previous_connected = connected
                previous_device_name = device_name

            except (
                OSError,
                urllib.error.URLError,
                urllib.error.HTTPError,
            ) as error:
                print(
                    f"TMBA-Backend nicht erreichbar: {error}",
                    flush=True,
                )

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
