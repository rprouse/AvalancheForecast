import urequests

from wifi import wifi_connect

wlan = wifi_connect()

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)

if response.status_code == 200:
    data = response.json()
    title = data['report']['title']
    print("Report title:", title)
    print()

    # Display danger ratings
    for danger_rating in data['report']['dangerRatings']:
        print(danger_rating['date']['display'])
        ratings = danger_rating['ratings']
        print("  " + ratings['alp']['display'] + ": " + ratings['alp']['rating']['display'])
        print("  " + ratings['tln']['display'] + ": " + ratings['tln']['rating']['display'])
        print("  " + ratings['btl']['display'] + ": " + ratings['btl']['rating']['display'])
        print()
else:
    print("Failed to fetch forecast data")
