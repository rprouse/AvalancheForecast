# tft_spi.py
# MicroPython SPI TFT driver supporting ILI9341 and ST7796S
#
# Features:
# - RGB565 drawing directly to GRAM (no full framebuffer)
# - Text (5x7), lines, rectangles, circles, filled shapes
# - RGB565 sprite blit
#
# Tested API assumptions:
# - MicroPython machine.SPI, machine.Pin
# - Optional: time.sleep_ms

from machine import Pin
import time
import tt7

# --- Common MIPI-DBI style commands (shared by both controllers) ---
_NOP      = 0x00
_SWRESET  = 0x01
_SLPOUT   = 0x11
_DISPON   = 0x29
_DISPOFF  = 0x28
_CASET    = 0x2A
_RASET    = 0x2B
_RAMWR    = 0x2C
_MADCTL   = 0x36
_COLMOD   = 0x3A
_INVON    = 0x21
_INVOFF   = 0x20

# MADCTL bits (common)
_MADCTL_MY  = 0x80
_MADCTL_MX  = 0x40
_MADCTL_MV  = 0x20
_MADCTL_BGR = 0x08

# RGB565 pixel format value for COLMOD
_COLMOD_16BIT = 0x55

def color565(r, g, b):
    """Convert 8-bit RGB to RGB565 (int 0..65535)."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

class TFTBase:
    """
    Base class providing core SPI TFT display functionality.

    This class implements controller-agnostic primitives for common
    MIPI-DBI style TFT panels, such as:

    - Low-level command/data writes over SPI
    - Window (column/row) addressing
    - Pixel, line, rectangle, circle, and filled-shape drawing
    - Basic 5x7 text rendering and RGB565 sprite blitting

    Concrete driver classes (for example :class:`ILI9341` and
    :class:`ST7796S`) inherit from :class:`TFTBase` and implement the
    controller-specific initialization sequence and MADCTL/rotation
    configuration while reusing the high-level drawing API exposed by
    this base class.

    Typical usage is to:

    1. Create a hardware SPI instance (e.g. ``machine.SPI``).
    2. Provide chip-select (CS), data/command (DC), optional reset (RST),
       and optional backlight (BL) pins, either as ``machine.Pin``
       objects or as pin numbers.
    3. Instantiate a concrete subclass with the appropriate panel width,
       height, rotation and color-order settings, then call its drawing
       methods to update the display.

    Advanced users adding support for new controllers should subclass
    :class:`TFTBase`, implement the required initialization and any
    controller-specific commands, and rely on the existing drawing and
    text methods where possible.
    """
    def __init__(self, spi, cs, dc, rst=None, bl=None,
                 width=0, height=0, rotation=0, bgr=True, invert=False):
        """
        spi: machine.SPI instance
        cs, dc, rst, bl: machine.Pin instances or pin numbers
        width,height: physical panel size for this controller
        rotation: 0..3
        bgr: True if panel expects BGR color order (common on many modules)
        invert: True to enable display inversion (module dependent)
        """
        self.spi = spi
        self.cs = cs if isinstance(cs, Pin) else Pin(cs, Pin.OUT, value=1)
        self.dc = dc if isinstance(dc, Pin) else Pin(dc, Pin.OUT, value=0)
        self.rst = None if rst is None else (rst if isinstance(rst, Pin) else Pin(rst, Pin.OUT, value=1))
        self.bl = None if bl is None else (bl if isinstance(bl, Pin) else Pin(bl, Pin.OUT, value=1))

        self._w = width
        self._h = height
        self._rotation = rotation & 3
        self._bgr = bool(bgr)
        self._invert = bool(invert)

        # Some panels use offsets (esp. certain 240x320 variants); keep hooks.
        self._xoff = 0
        self._yoff = 0

        # Default font
        self._font = tt7

        # Reusable small buffer for solid fills (RGB565)
        self._chunk = bytearray(2 * 64)  # 64 pixels worth

    # --- Low-level bus ---
    def _select(self):
        self.cs(0)

    def _deselect(self):
        self.cs(1)

    def _cmd(self, c):
        self.dc(0)
        self._select()
        self.spi.write(bytearray([c & 0xFF]))
        self._deselect()

    def _data(self, buf):
        self.dc(1)
        self._select()
        self.spi.write(buf)
        self._deselect()

    def _cmd_data(self, c, data=b""):
        self._cmd(c)
        if data:
            self._data(data)

    def reset(self):
        if self.rst is None:
            return
        self.rst(1)
        time.sleep_ms(10)
        self.rst(0)
        time.sleep_ms(20)
        self.rst(1)
        time.sleep_ms(120)

    def set_font(self, font):
        """
        Set the font to use for text rendering.

        :param font: Font module implementing get_ch(), height(), and max_width() methods.
                     Examples: tt7, tt14, tt24, tt32
        """
        self._font = font

    # --- Addressing / rotation ---
    @property
    def width(self):
        return self._w if (self._rotation & 1) == 0 else self._h

    @property
    def height(self):
        return self._h if (self._rotation & 1) == 0 else self._w

    def rotation(self, r):
        self._rotation = r & 3
        self._apply_madctl()

    def _apply_madctl(self):
        r = self._rotation
        mad = 0
        if r == 0:
            mad = _MADCTL_MX
        elif r == 1:
            mad = _MADCTL_MV
        elif r == 2:
            mad = _MADCTL_MY
        elif r == 3:
            mad = _MADCTL_MX | _MADCTL_MY | _MADCTL_MV
        if self._bgr:
            mad |= _MADCTL_BGR
        self._cmd_data(_MADCTL, bytes([mad]))

    def _set_window(self, x0, y0, x1, y1):
        # Apply offsets
        x0 += self._xoff
        x1 += self._xoff
        y0 += self._yoff
        y1 += self._yoff

        # CASET/RASET want big-endian 16-bit
        self._cmd_data(_CASET, bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._cmd_data(_RASET, bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._cmd(_RAMWR)

    # --- Common init steps (controller-specific init tables call into these) ---
    def common_init(self):
        self.reset()
        self._cmd(_SWRESET)
        time.sleep_ms(120)
        self._cmd(_SLPOUT)
        time.sleep_ms(120)

        # Pixel format RGB565
        self._cmd_data(_COLMOD, bytes([_COLMOD_16BIT]))
        time.sleep_ms(10)

        self._apply_madctl()

        if self._invert:
            self._cmd(_INVON)
        else:
            self._cmd(_INVOFF)

        self._cmd(_DISPON)
        time.sleep_ms(50)

        if self.bl is not None:
            self.bl(1)

    # --- Drawing primitives ---
    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def erase(self):
        self.fill(0x0000)  # Black

    def pixel(self, x, y, color):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        self._set_window(x, y, x, y)
        self._data(bytes([color >> 8, color & 0xFF]))

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        x1 = x + w - 1
        y1 = y + h - 1
        if x1 < 0 or y1 < 0 or x >= self.width or y >= self.height:
            return
        # Clip
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y

        self._set_window(x, y, x + w - 1, y + h - 1)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF

        # Fill chunk buffer with repeated color
        chunk = self._chunk
        for i in range(0, len(chunk), 2):
            chunk[i] = hi
            chunk[i + 1] = lo

        total = w * h
        self.dc(1)
        self._select()
        # Stream as many full chunks as possible
        while total > 0:
            n = 64 if total >= 64 else total
            self.spi.write(chunk[:2 * n])
            total -= n
        self._deselect()

    def line(self, x0, y0, x1, y1, color):
        # Bresenham
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, x0, y0, r, color):
        # Midpoint circle
        x = r
        y = 0
        err = 1 - r
        while x >= y:
            self.pixel(x0 + x, y0 + y, color)
            self.pixel(x0 + y, y0 + x, color)
            self.pixel(x0 - y, y0 + x, color)
            self.pixel(x0 - x, y0 + y, color)
            self.pixel(x0 - x, y0 - y, color)
            self.pixel(x0 - y, y0 - x, color)
            self.pixel(x0 + y, y0 - x, color)
            self.pixel(x0 + x, y0 - y, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    def fill_circle(self, x0, y0, r, color):
        # Scanline fill using midpoint
        x = r
        y = 0
        err = 1 - r
        while x >= y:
            self.hline(x0 - x, y0 + y, 2 * x + 1, color)
            self.hline(x0 - x, y0 - y, 2 * x + 1, color)
            self.hline(x0 - y, y0 + x, 2 * y + 1, color)
            self.hline(x0 - y, y0 - x, 2 * y + 1, color)
            y += 1
            if err < 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1

    # --- Text rendering ---
    def text(self, s, x, y, color, bg=None, scale=1, spacing=1):
        """
        Draw ASCII text using current font.
        bg=None means transparent background.
        scale=1..N scales glyph pixels.
        """
        font_height = self._font.height()
        cx = x
        for ch in s:
            if ch == "\n":
                cx = x
                y += (font_height * scale) + 2
                continue
            char_width = self._draw_char(ch, cx, y, color, bg, scale)
            cx += char_width + spacing

    def _draw_char(self, ch, x, y, color, bg, scale):
        # Get glyph data and width from font
        glyph, char_width = self._font.get_ch(ch)
        font_height = self._font.height()

        # Calculate bytes per column (height / 8, rounded up)
        bytes_per_col = (font_height + 7) // 8

        # Fast path: scale==1 and bg is not None => stream a tile (incl spacing row/col)
        if scale == 1 and bg is not None:
            w, h = char_width + 1, font_height + 1
            self._set_window(x, y, x + w - 1, y + h - 1)
            # Build a small RGB565 buffer for the tile
            buf = bytearray(w * h * 2)
            fg_hi, fg_lo = (color >> 8) & 0xFF, color & 0xFF
            bg_hi, bg_lo = (bg >> 8) & 0xFF, bg & 0xFF

            # Fill background
            for i in range(0, len(buf), 2):
                buf[i] = bg_hi
                buf[i + 1] = bg_lo

            # Plot glyph - glyph data format: [col0_byte0, col0_byte1, ..., col1_byte0, col1_byte1, ...]
            for col in range(char_width):
                for row in range(font_height):
                    byte_idx = row // 8
                    bit_idx = row % 8
                    glyph_idx = col * bytes_per_col + byte_idx
                    if glyph_idx < len(glyph):
                        bits = glyph[glyph_idx]
                        if bits & (1 << bit_idx):
                            p = (row * w + col) * 2
                            buf[p] = fg_hi
                            buf[p + 1] = fg_lo

            self._data(buf)
            return char_width * scale

        # General path: plot scaled pixels (transparent or scaled)
        for col in range(char_width):
            for row in range(font_height):
                byte_idx = row // 8
                bit_idx = row % 8
                glyph_idx = col * bytes_per_col + byte_idx
                on = False
                if glyph_idx < len(glyph):
                    bits = glyph[glyph_idx]
                    on = bits & (1 << bit_idx)

                if on:
                    if scale == 1:
                        self.pixel(x + col, y + row, color)
                    else:
                        self.fill_rect(x + col * scale, y + row * scale, scale, scale, color)
                elif bg is not None:
                    if scale == 1:
                        self.pixel(x + col, y + row, bg)
                    else:
                        self.fill_rect(x + col * scale, y + row * scale, scale, scale, bg)
        # Optional spacing column
        if bg is not None:
            if scale == 1:
                self.vline(x + char_width, y, font_height, bg)
                self.hline(x, y + font_height, char_width + 1, bg)
            else:
                self.fill_rect(x + char_width * scale, y, scale, font_height * scale, bg)
                self.fill_rect(x, y + font_height * scale, (char_width + 1) * scale, scale, bg)

        return char_width * scale

    # --- Sprites ---
    def blit_rgb565(self, x, y, w, h, data, key=None):
        """
        Blit a raw RGB565 sprite to the display.
        - data: bytes/bytearray of length w*h*2, big-endian RGB565 per pixel.
        - key: optional transparency key color (RGB565 int). If provided, this
               function falls back to per-pixel plotting (slower).
        """
        if w <= 0 or h <= 0:
            return
        if key is None:
            # Fast: set window and stream data
            self._set_window(x, y, x + w - 1, y + h - 1)
            self._data(data)
            return

        # Slow path: transparency key
        # data must be big-endian pairs
        i = 0
        for yy in range(h):
            for xx in range(w):
                c = (data[i] << 8) | data[i + 1]
                if c != key:
                    self.pixel(x + xx, y + yy, c)
                i += 2


class ILI9341(TFTBase):
    """
    Driver for ILI9341-based TFT displays with 240x320 resolution.

    The ILI9341 is a popular TFT LCD controller supporting up to 240x320
    RGB pixels in 16-bit color mode. This driver uses a minimal initialization
    sequence via :meth:`common_init` for broad module compatibility, performing:

    - Hardware and software reset
    - Sleep out command
    - RGB565 pixel format configuration
    - MADCTL (rotation and color order) setup
    - Display inversion control
    - Display on

    The ILI9341 does not require controller-specific command sequences,
    making it compatible with a wide range of modules. Optional frame rate
    and porch settings are intentionally omitted to maximize compatibility.

    :param spi: Configured SPI bus instance
    :param cs: Chip select pin (Pin object or pin number)
    :param dc: Data/command control pin (Pin object or pin number)
    :param rst: Optional reset pin (Pin object or pin number)
    :param bl: Optional backlight control pin (Pin object or pin number)
    :param rotation: Display rotation (0-3, default 0)
    :param bgr: Use BGR color order if True, RGB if False (default True)
    :param invert: Enable display inversion if True (default False)
    """
    def __init__(self, spi, cs, dc, rst=None, bl=None,
                 rotation=0, bgr=True, invert=False):
        super().__init__(spi, cs, dc, rst=rst, bl=bl,
                         width=240, height=320,
                         rotation=rotation, bgr=bgr, invert=invert)

    def init(self):
        # Common reset / sleep out / colmod / madctl / disp on
        self.common_init()

        # Optional: some modules need different porch/frame settings.
        # Keep minimal for broad compatibility.


class ST7796S(TFTBase):
    """
    Driver for ST7796S TFT display controller (320x480 resolution).

    The ST7796S is commonly used in 3.5" and 4.0" TFT LCD modules with
    a native resolution of 320x480 pixels in RGB565 color mode.

    Key differences from ILI9341:
    - Higher resolution: 320x480 vs 240x320
    - Requires Command Set Control (CSCON) unlock sequence during
      initialization (0xF0 commands) for proper module compatibility
    - Uses extended command set initialization common to ST77xx family

    Initialization sequence includes:
    1. Hardware/software reset
    2. Command Set Control unlock (0xF0 register writes)
    3. Sleep out, color mode, MADCTL, display on
    4. Optional backlight control

    Usage is identical to ILI9341 once initialized.
    """
    def __init__(self, spi, cs, dc, rst=None, bl=None,
                 rotation=0, bgr=True, invert=False):
        super().__init__(spi, cs, dc, rst=rst, bl=bl,
                         width=320, height=480,
                         rotation=rotation, bgr=bgr, invert=invert)

    def init(self):
        # ST7796S often expects a command-set control unlock sequence (F0).
        # Many modules work without it; enabling it improves compatibility.
        self.reset()
        self._cmd(_SWRESET)
        time.sleep_ms(120)

        # Command Set Control (CSCON / F0h) - common module init practice
        # This sequence is widely used on ST77xx-family modules.
        self._cmd_data(0xF0, b"\xC3")
        self._cmd_data(0xF0, b"\x96")

        # Sleep out
        self._cmd(_SLPOUT)
        time.sleep_ms(120)

        # RGB565
        self._cmd_data(_COLMOD, bytes([_COLMOD_16BIT]))
        time.sleep_ms(10)

        self._apply_madctl()

        if self._invert:
            self._cmd(_INVON)
        else:
            self._cmd(_INVOFF)

        self._cmd(_DISPON)
        time.sleep_ms(50)

        if self.bl is not None:
            self.bl(1)
