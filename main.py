import urequests

from wifi import wifi_connect

from tft_spi import ILI9341, color565
from machine import Pin, SPI
import os

# Common colors
WHITE = color565(0xFF, 0xFF, 0xFF)
GRAY = color565(0xF8, 0xF8, 0xF8)
BLACK = color565(0x00, 0x00, 0x00)
ALP = WHITE
TLN = color565(0xC1, 0xD8, 0x31)
BTL = color565(0x6E, 0xA4, 0x69)

# Danger rating colors from the website
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

SCR_WIDTH = const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

TFT_CLK_PIN = const(6)
TFT_MOSI_PIN = const(7)
TFT_MISO_PIN = const(4)

TFT_CS_PIN = const(13)
TFT_RST_PIN = const(14)
TFT_DC_PIN = const(15)

def initialize_display():
    spi = SPI(
        0,
        baudrate=40000000,
        miso=Pin(TFT_MISO_PIN),
        mosi=Pin(TFT_MOSI_PIN),
        sck=Pin(TFT_CLK_PIN))
    print(spi)

    cs  = Pin(TFT_CS_PIN, Pin.OUT)
    dc  = Pin(TFT_DC_PIN, Pin.OUT)
    rst = Pin(TFT_RST_PIN, Pin.OUT)

    tft = ILI9341(spi, cs, dc, rst=rst, rotation=SCR_ROT, bgr=True, invert=False)

    tft.init()
    tft.fill(BLACK)
    return tft

def display_forecast(tft,today, y):
    tft.text(today['date']['display'], 10, y, GRAY, scale=2)

    y = y + 18
    rating = today['ratings']['alp']['rating']['value']
    tft.fill_rect(10, y, 100, 16, ALP)
    tft.text("Alpine", 14, y + 4, BLACK)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['alp']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating])

    y = y + 18
    rating = today['ratings']['tln']['rating']['value']
    tft.fill_rect(10, y, 100, 16, TLN)
    tft.text("Treeline", 14, y + 4, BLACK)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['tln']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating])

    y = y + 18
    rating = today['ratings']['btl']['rating']['value']
    tft.fill_rect(10, y, 100, 16, BTL)
    tft.text("Below Treeline", 14, y + 4, BLACK)
    tft.fill_rect(112, y, 100, 16, DANGER_BG_COLORS[rating])
    tft.text(today['ratings']['btl']['rating']['display'], 116,  y + 4, DANGER_FG_COLORS[rating])

    return y + 24

def main():
    print(os.uname())
    wlan = wifi_connect()
    tft = initialize_display()

    # Fetch avalanche forecast data from the Avalanche Canada API
    response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
    print("Response status:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        title = data['report']['title']
        # display.set_font(tt14)
        # display.set_color(color565(0, 255, 255), color565(0, 0, 0))
        # display.print(title + "\n")

        # Display danger ratings
        y = 10
        for danger_rating in data['report']['dangerRatings']:
            y = display_forecast(tft, danger_rating, y)

    else:
        tft.text("Failed to fetch forecast data", 10, 10, WHITE, scale=2)

    response.close()

if __name__ == "__main__":
    main()
