from drivers.tft_spi import color565

# Common colors
WHITE = color565(0xFF, 0xFF, 0xFF)
GRAY = color565(0xF8, 0xF8, 0xF8)
BLACK = color565(0x00, 0x00, 0x00)
GREEN = color565(0x00, 0xFF, 0x00)
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
