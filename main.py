import urequests

from wifi import wifi_connect

wlan = wifi_connect()

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)
print("Response JSON:", response.json())
