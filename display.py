from ili9341 import Display
from machine import Pin, SPI  # type: ignore
from xglcd_font import XglcdFont

def initialize_display():
    print('Initializing display...')
    TFT_CLK_PIN = const(6)
    TFT_MOSI_PIN = const(7)
    TFT_MISO_PIN = const(4)

    TFT_CS_PIN = const(13)
    TFT_RST_PIN = const(14)
    TFT_DC_PIN = const(15)

    # Baud rate of 40000000 seems about the max
    #spi = SPI(1, baudrate=40000000, sck=Pin(6), mosi=Pin(7))

    spi = SPI(
        0,
        baudrate=40000000,
        miso=Pin(TFT_MISO_PIN),
        mosi=Pin(TFT_MOSI_PIN),
        sck=Pin(TFT_CLK_PIN))

    return Display(spi, dc=Pin(TFT_DC_PIN), cs=Pin(TFT_CS_PIN), rst=Pin(TFT_RST_PIN), rotation=180)

def load_display_fonts():
    print('Loading fonts...')

    print('  Loading arcadepix')
    arcadepix = XglcdFont('ArcadePix9x11.c', 9, 11)

    print('  Loading bally')
    bally = XglcdFont('Bally7x9.c', 7, 9)

    print('  Loading dejavu')
    dejavu = XglcdFont('Dejavu24x43.c', 24, 43)

    print('  Loading fixed_font')
    fixed_font = XglcdFont('FixedFont5x8.c', 5, 8)

    print('  Loading unispace')
    unispace = XglcdFont('Unispace12x24.c', 12, 24)

    print('  Loading wendy')
    wendy = XglcdFont('Wendy7x8.c', 7, 8)

    fonts = [arcadepix, bally, dejavu, fixed_font, unispace, wendy]

    print('Fonts loaded.')

    return fonts
