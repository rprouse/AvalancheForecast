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

# Minimal 5x7 font (ASCII 32..127), stored column-wise.
# Each glyph is 5 bytes, each byte is 7 LSB bits (top->bottom).
# This is a compact, standard public-domain style bitmap.
_FONT_5X7 = bytes([
    # 32 ' '
    0x00,0x00,0x00,0x00,0x00,
    # 33 '!'
    0x00,0x00,0x5F,0x00,0x00,
    # 34 '"'
    0x00,0x07,0x00,0x07,0x00,
    # 35 '#'
    0x14,0x7F,0x14,0x7F,0x14,
    # 36 '$'
    0x24,0x2A,0x7F,0x2A,0x12,
    # 37 '%'
    0x23,0x13,0x08,0x64,0x62,
    # 38 '&'
    0x36,0x49,0x55,0x22,0x50,
    # 39 "'"
    0x00,0x05,0x03,0x00,0x00,
    # 40 '('
    0x00,0x1C,0x22,0x41,0x00,
    # 41 ')'
    0x00,0x41,0x22,0x1C,0x00,
    # 42 '*'
    0x14,0x08,0x3E,0x08,0x14,
    # 43 '+'
    0x08,0x08,0x3E,0x08,0x08,
    # 44 ','
    0x00,0x50,0x30,0x00,0x00,
    # 45 '-'
    0x08,0x08,0x08,0x08,0x08,
    # 46 '.'
    0x00,0x60,0x60,0x00,0x00,
    # 47 '/'
    0x20,0x10,0x08,0x04,0x02,
    # 48 '0'
    0x3E,0x51,0x49,0x45,0x3E,
    # 49 '1'
    0x00,0x42,0x7F,0x40,0x00,
    # 50 '2'
    0x42,0x61,0x51,0x49,0x46,
    # 51 '3'
    0x21,0x41,0x45,0x4B,0x31,
    # 52 '4'
    0x18,0x14,0x12,0x7F,0x10,
    # 53 '5'
    0x27,0x45,0x45,0x45,0x39,
    # 54 '6'
    0x3C,0x4A,0x49,0x49,0x30,
    # 55 '7'
    0x01,0x71,0x09,0x05,0x03,
    # 56 '8'
    0x36,0x49,0x49,0x49,0x36,
    # 57 '9'
    0x06,0x49,0x49,0x29,0x1E,
    # 58 ':'
    0x00,0x36,0x36,0x00,0x00,
    # 59 ';'
    0x00,0x56,0x36,0x00,0x00,
    # 60 '<'
    0x08,0x14,0x22,0x41,0x00,
    # 61 '='
    0x14,0x14,0x14,0x14,0x14,
    # 62 '>'
    0x00,0x41,0x22,0x14,0x08,
    # 63 '?'
    0x02,0x01,0x51,0x09,0x06,
    # 64 '@'
    0x32,0x49,0x79,0x41,0x3E,
    # 65 'A'
    0x7E,0x11,0x11,0x11,0x7E,
    # 66 'B'
    0x7F,0x49,0x49,0x49,0x36,
    # 67 'C'
    0x3E,0x41,0x41,0x41,0x22,
    # 68 'D'
    0x7F,0x41,0x41,0x22,0x1C,
    # 69 'E'
    0x7F,0x49,0x49,0x49,0x41,
    # 70 'F'
    0x7F,0x09,0x09,0x09,0x01,
    # 71 'G'
    0x3E,0x41,0x49,0x49,0x7A,
    # 72 'H'
    0x7F,0x08,0x08,0x08,0x7F,
    # 73 'I'
    0x00,0x41,0x7F,0x41,0x00,
    # 74 'J'
    0x20,0x40,0x41,0x3F,0x01,
    # 75 'K'
    0x7F,0x08,0x14,0x22,0x41,
    # 76 'L'
    0x7F,0x40,0x40,0x40,0x40,
    # 77 'M'
    0x7F,0x02,0x0C,0x02,0x7F,
    # 78 'N'
    0x7F,0x04,0x08,0x10,0x7F,
    # 79 'O'
    0x3E,0x41,0x41,0x41,0x3E,
    # 80 'P'
    0x7F,0x09,0x09,0x09,0x06,
    # 81 'Q'
    0x3E,0x41,0x51,0x21,0x5E,
    # 82 'R'
    0x7F,0x09,0x19,0x29,0x46,
    # 83 'S'
    0x46,0x49,0x49,0x49,0x31,
    # 84 'T'
    0x01,0x01,0x7F,0x01,0x01,
    # 85 'U'
    0x3F,0x40,0x40,0x40,0x3F,
    # 86 'V'
    0x1F,0x20,0x40,0x20,0x1F,
    # 87 'W'
    0x3F,0x40,0x38,0x40,0x3F,
    # 88 'X'
    0x63,0x14,0x08,0x14,0x63,
    # 89 'Y'
    0x07,0x08,0x70,0x08,0x07,
    # 90 'Z'
    0x61,0x51,0x49,0x45,0x43,
    # 91 '['
    0x00,0x7F,0x41,0x41,0x00,
    # 92 '\'
    0x02,0x04,0x08,0x10,0x20,
    # 93 ']'
    0x00,0x41,0x41,0x7F,0x00,
    # 94 '^'
    0x04,0x02,0x01,0x02,0x04,
    # 95 '_'
    0x40,0x40,0x40,0x40,0x40,
    # 96 '`'
    0x00,0x01,0x02,0x04,0x00,
    # 97 'a'
    0x20,0x54,0x54,0x54,0x78,
    # 98 'b'
    0x7F,0x48,0x44,0x44,0x38,
    # 99 'c'
    0x38,0x44,0x44,0x44,0x20,
    # 100 'd'
    0x38,0x44,0x44,0x48,0x7F,
    # 101 'e'
    0x38,0x54,0x54,0x54,0x18,
    # 102 'f'
    0x08,0x7E,0x09,0x01,0x02,
    # 103 'g'
    0x0C,0x52,0x52,0x52,0x3E,
    # 104 'h'
    0x7F,0x08,0x04,0x04,0x78,
    # 105 'i'
    0x00,0x44,0x7D,0x40,0x00,
    # 106 'j'
    0x20,0x40,0x44,0x3D,0x00,
    # 107 'k'
    0x7F,0x10,0x28,0x44,0x00,
    # 108 'l'
    0x00,0x41,0x7F,0x40,0x00,
    # 109 'm'
    0x7C,0x04,0x18,0x04,0x78,
    # 110 'n'
    0x7C,0x08,0x04,0x04,0x78,
    # 111 'o'
    0x38,0x44,0x44,0x44,0x38,
    # 112 'p'
    0x7C,0x14,0x14,0x14,0x08,
    # 113 'q'
    0x08,0x14,0x14,0x18,0x7C,
    # 114 'r'
    0x7C,0x08,0x04,0x04,0x08,
    # 115 's'
    0x48,0x54,0x54,0x54,0x20,
    # 116 't'
    0x04,0x3F,0x44,0x40,0x20,
    # 117 'u'
    0x3C,0x40,0x40,0x20,0x7C,
    # 118 'v'
    0x1C,0x20,0x40,0x20,0x1C,
    # 119 'w'
    0x3C,0x40,0x30,0x40,0x3C,
    # 120 'x'
    0x44,0x28,0x10,0x28,0x44,
    # 121 'y'
    0x0C,0x50,0x50,0x50,0x3C,
    # 122 'z'
    0x44,0x64,0x54,0x4C,0x44,
    # 123 '{'
    0x00,0x08,0x36,0x41,0x00,
    # 124 '|'
    0x00,0x00,0x7F,0x00,0x00,
    # 125 '}'
    0x00,0x41,0x36,0x08,0x00,
    # 126 '~'
    0x08,0x08,0x2A,0x1C,0x08,
    # 127 DEL (unused)
    0x00,0x00,0x00,0x00,0x00,
])

class TFTBase:
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
        Draw ASCII text using 5x7 font.
        bg=None means transparent background.
        scale=1..N scales glyph pixels.
        """
        cx = x
        for ch in s:
            if ch == "\n":
                cx = x
                y += (7 * scale) + 2
                continue
            self._draw_char(ch, cx, y, color, bg, scale)
            cx += (5 * scale) + spacing

    def _draw_char(self, ch, x, y, color, bg, scale):
        code = ord(ch)
        if code < 32 or code > 127:
            code = 32
        idx = (code - 32) * 5
        glyph = _FONT_5X7[idx:idx + 5]

        # Fast path: scale==1 and bg is not None => stream a 6x8 tile (incl spacing row/col)
        # We render 5x7, but include 1px column/row spacing so text doesn't touch.
        if scale == 1 and bg is not None:
            w, h = 6, 8
            self._set_window(x, y, x + w - 1, y + h - 1)
            # Build a small RGB565 buffer for the tile
            buf = bytearray(w * h * 2)
            fg_hi, fg_lo = (color >> 8) & 0xFF, color & 0xFF
            bg_hi, bg_lo = (bg >> 8) & 0xFF, bg & 0xFF

            # Fill background
            for i in range(0, len(buf), 2):
                buf[i] = bg_hi
                buf[i + 1] = bg_lo

            # Plot glyph
            for col in range(5):
                bits = glyph[col]
                for row in range(7):
                    if bits & (1 << row):
                        p = (row * w + col) * 2
                        buf[p] = fg_hi
                        buf[p + 1] = fg_lo

            self._data(buf)
            return

        # General path: plot scaled pixels (transparent or scaled)
        for col in range(5):
            bits = glyph[col]
            for row in range(7):
                on = bits & (1 << row)
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
                self.vline(x + 5, y, 7, bg)
                self.hline(x, y + 7, 6, bg)
            else:
                self.fill_rect(x + 5 * scale, y, scale, 7 * scale, bg)
                self.fill_rect(x, y + 7 * scale, 6 * scale, scale, bg)

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
