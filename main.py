import urequests

from wifi import wifi_connect

from tft_spi import ILI9341, color565
#from ili934xnew import ILI9341, color565
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

# Common colors
WHITE = color565(255, 255, 255)
BLACK = color565(0, 0, 0)
ALP = WHITE
TLN = color565(0xC1, 0xD8, 0x31)
BTL = color565(0x6E, 0xA4, 0x69)

# Danger rating colors
DANGER_BG_COLORS = {
    "low": color565(80, 184, 72),
    "moderate": color565(255, 242, 0),
    "considerable": color565(247, 148, 30),
    "high": color565(237, 28, 36),
    "extreme": color565(35, 31, 32)
}

DANGER_FG_COLORS = {
    "low": BLACK,
    "moderate": BLACK,
    "considerable": BLACK,
    "high": BLACK,
    "extreme": WHITE
}

cs  = Pin(TFT_CS_PIN, Pin.OUT)
dc  = Pin(TFT_DC_PIN, Pin.OUT)
rst = Pin(TFT_RST_PIN, Pin.OUT)

tft = ILI9341(spi, cs, dc, rst=rst, rotation=SCR_ROT, bgr=True, invert=False)

tft.init()
tft.fill(color565(0, 0, 0))
# tft.set_pos(0,0)
# tft.set_font(tt14)

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)

if response.status_code == 200:
    data = response.json()
    # title = data['report']['title']
    # display.set_font(tt14)
    # display.set_color(color565(0, 255, 255), color565(0, 0, 0))
    # display.print(title + "\n")

    # # Display danger ratings
    # for danger_rating in data['report']['dangerRatings']:
    #     display.set_font(tt24)
    #     display.set_color(color565(0, 0, 255), color565(0, 0, 0))
    #     display.print(danger_rating['date']['display'])
    #     ratings = danger_rating['ratings']

    #     display.set_font(tt14)
    #     display.set_color(color565(0, 255, 0), color565(0, 0, 0))
    #     display.print("  " + ratings['alp']['display'] + ": " + ratings['alp']['rating']['display'])
    #     display.print("  " + ratings['tln']['display'] + ": " + ratings['tln']['rating']['display'])
    #     display.print("  " + ratings['btl']['display'] + ": " + ratings['btl']['rating']['display'])
    #     display.print("")

    y = 10;
    today = data['report']['dangerRatings'][0];
    tft.text(today['date']['display'], 10, 10, WHITE, bg=None, scale=2)

    y = y + 18
    rating = today['ratings']['alp']['rating']['value']
    tft.fill_rect(10, y, 100, 16, ALP)
    tft.text("Alpine", 14, y + 4, BLACK, bg=None, scale=1)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['alp']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating], bg=None, scale=1)

    y = y + 18
    rating = today['ratings']['tln']['rating']['value']
    tft.fill_rect(10, y, 100, 16, TLN)
    tft.text("Treeline", 14, y + 4, BLACK, bg=None, scale=1)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['tln']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating], bg=None, scale=1)

    y = y + 18
    rating = today['ratings']['btl']['rating']['value']
    tft.fill_rect(10, y, 100, 16, BTL)
    tft.text("Below Treeline", 14, y + 4, BLACK, bg=None, scale=1)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['btl']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating], bg=None, scale=1)
else:
    tft.text("Failed to fetch forecast data", 10, 10, color565(255, 255, 255), bg=None, scale=2)

response.close()
