import network
import time
import rp2

_STATUS_TEXT = {
    network.STAT_IDLE:           "IDLE",
    network.STAT_CONNECTING:     "CONNECTING",
    network.STAT_WRONG_PASSWORD: "WRONG_PASSWORD",
    network.STAT_NO_AP_FOUND:    "NO_AP_FOUND",
    network.STAT_CONNECT_FAIL:   "CONNECT_FAIL",
    network.STAT_GOT_IP:         "CONNECTED",
}

def _status_text(code: int) -> str:
    return _STATUS_TEXT.get(code, f"UNKNOWN({code})")

def connect_wifi(
    ssid: str,
    password: str,
    *,
    timeout_s: float = 15.0,
    country: str | None = "CA",   # set to None to skip
    poll_ms: int = 250,
    verbose: bool = True,
) -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Optional but recommended on Pico W.
    if country is not None:
        try:
            rp2.country(country)
            if verbose:
                print(f"[wifi] country set to {country}")
        except Exception as e:
            # Not all builds expose this; fail soft.
            if verbose:
                print(f"[wifi] country set failed: {e!r}")

    # If already connected to the right AP, just return.
    if wlan.isconnected():
        if verbose:
            print("[wifi] already connected:", wlan.ifconfig())
        return wlan

    if verbose:
        print(f"[wifi] connecting to SSID={ssid!r} ...")

    wlan.connect(ssid, password)

    deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
    last_status = None

    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        status = wlan.status()

        # Only print when status changes (keeps logs readable)
        if verbose and status != last_status:
            print(f"[wifi] status={status} {_status_text(status)}")
            last_status = status

        if status == network.STAT_GOT_IP or wlan.isconnected():
            if verbose:
                print("[wifi] connected:", wlan.ifconfig())
            return wlan

        # Any negative value is a terminal error on MicroPython WLAN.
        if status < 0:
            if verbose:
                print(f"[wifi] ERROR: status={status} {_status_text(status)}")
            try:
                wlan.disconnect()
            except Exception:
                pass
            raise OSError(f"WiFi connect failed: {status} {_status_text(status)}")

        time.sleep_ms(poll_ms)

    # Timeout
    if verbose:
        print(f"[wifi] TIMEOUT after {timeout_s:.1f}s, last status={wlan.status()} {_status_text(wlan.status())}")
    try:
        wlan.disconnect()
    except Exception:
        pass
    raise TimeoutError("WiFi connect timed out")


# Example usage:
# wlan = connect_wifi("MySSID", "MyPassword", timeout_s=20, country="CA", verbose=True)
