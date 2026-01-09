import urequests

from wifi import wifi_connect

from ili934xnew import ILI9341, color565
from machine import Pin, SPI
from machine import idle, Pin, SPI  # type: ignore
import os
import glcdfont
import tt14
import tt24
import tt32

SCR_WIDTH = const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

print(os.uname())
TFT_CLK_PIN = const(6)
TFT_MOSI_PIN = const(7)
TFT_MISO_PIN = const(4)

TFT_CS_PIN = const(13)
TFT_RST_PIN = const(14)
TFT_DC_PIN = const(15)

wlan = wifi_connect()

spi = SPI(
    0,
    baudrate=40000000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN))
print(spi)

display = ILI9341(
    spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT)

display.erase()
display.set_pos(0,0)
display.set_font(tt14)

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)

if response.status_code == 200:
    data = response.json()
    title = data['report']['title']
    display.set_font(tt14)
    display.set_color(color565(0, 255, 255), color565(0, 0, 0))
    display.print(title + "\n")

    # Display danger ratings
    for danger_rating in data['report']['dangerRatings']:
        display.set_font(tt24)
        display.set_color(color565(0, 0, 255), color565(0, 0, 0))
        display.print(danger_rating['date']['display'])
        ratings = danger_rating['ratings']

        display.set_font(tt14)
        display.set_color(color565(0, 255, 0), color565(0, 0, 0))
        display.print("  " + ratings['alp']['display'] + ": " + ratings['alp']['rating']['display'])
        display.print("  " + ratings['tln']['display'] + ": " + ratings['tln']['rating']['display'])
        display.print("  " + ratings['btl']['display'] + ": " + ratings['btl']['rating']['display'])
        display.print("")
else:
    display.print("Failed to fetch forecast data")

