# Pin definitions for the TFT display and touch controller
from machine import Pin

TFT_CLK_PIN = const(6)
TFT_MOSI_PIN = const(7)
TFT_MISO_PIN = const(4)

TFT_CS_PIN = const(13)
TFT_RST_PIN = const(14)
TFT_DC_PIN = const(15)

TOUCH_CLK_PIN = const(10)
TOUCH_MOSI_PIN = const(11)
TOUCH_MISO_PIN = const(8)
TOUCH_CS_PIN = const(12)
TOUCH_INT_PIN = const(0) # Not supported on the Pico Breadboard Kit