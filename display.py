from drivers.tft_spi import ILI9341, TFTBase
from machine import Pin, SPI
import pins

SCR_WIDTH = const(240)
SCR_HEIGHT = const(360)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

def initialize() -> TFTBase:
    """
    Initialize the ILI9341 TFT display and clear the screen to black.

    Configures the SPI bus and control pins, instantiates and initializes the
    ILI9341 display driver, and clears the display.

    Side effects:
        Prints the configured SPI object to the console.

    Returns:
        ILI9341: An initialized TFT display object ready for drawing.
    """
    spi = SPI(
        0,
        baudrate=40000000,
        miso=Pin(pins.TFT_MISO_PIN),
        mosi=Pin(pins.TFT_MOSI_PIN),
        sck=Pin(pins.TFT_CLK_PIN))
    print(spi)

    cs  = Pin(pins.TFT_CS_PIN, Pin.OUT)
    dc  = Pin(pins.TFT_DC_PIN, Pin.OUT)
    rst = Pin(pins.TFT_RST_PIN, Pin.OUT)

    tft = ILI9341(spi, cs, dc, rst=rst, rotation=SCR_ROT, bgr=True, invert=False)

    tft.init()
    tft.erase()
    return tft
