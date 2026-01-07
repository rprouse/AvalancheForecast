import time
import network
import rp2
import urequests

from secrets import SSID, PASSWORD

def wifi_connect(timeout_s=10, country="CA"):
    # If you have flaky connects, set your regulatory domain (country)
    # (Example in docs shows rp2.country('GB')).:contentReference[oaicite:2]{index=2}
    rp2.country(country)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    # Wait for connect or fail (docs pattern).:contentReference[oaicite:3]{index=3}
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        s = wlan.status()
        if s < 0 or s >= 3:
            break
        time.sleep(1)

    if wlan.status() != 3:
        # Status codes are: 3=up, -3=badauth, -2=nonet, -1=fail, etc.:contentReference[oaicite:4]{index=4}
        raise RuntimeError("WiFi failed, status=%d" % wlan.status())

    print("WiFi connected:", wlan.ifconfig())  # (ip, netmask, gw, dns)
    return wlan

wlan = wifi_connect()

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)
print("Response JSON:", response.json())
