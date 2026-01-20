from machine import SPI, Pin
from micropython import const
import tft_spi
import fonts.tt7, fonts.tt14, fonts.tt24

SCR_ROT = const(2)

TFT_CLK_PIN = const(6)
TFT_MOSI_PIN = const(7)
TFT_MISO_PIN = const(4)

TFT_CS_PIN = const(13)
TFT_RST_PIN = const(14)
TFT_DC_PIN = const(15)

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

# Pick ONE:
tft = tft_spi.ILI9341(spi, cs, dc, rst=rst, rotation=SCR_ROT, bgr=True, invert=False)
# tft = tft_spi.ST7796S(spi, cs, dc, rst=rst, rotation=1, bgr=True, invert=False)

tft.init()
tft.fill(tft_spi.color565(0, 0, 0))

white = tft_spi.color565(255, 255, 255)
green = tft_spi.color565(0, 255, 0)

tft.text("Small", 10, 10, white)

# Switch to larger font
tft.set_font(fonts.tt14)
tft.text("Medium", 10, 30, tft_spi.color565(255, 255, 255))

tft.set_font(fonts.tt24)
tft.text("Large", 10, 60, tft_spi.color565(255, 255, 255))

tft.rect(5, 160, 120, 40, green)
tft.line(0, 0, tft.width - 1, tft.height - 1, green)
tft.fill_circle(80, 120, 30, tft_spi.color565(255, 0, 0))
