#!/usr/bin/env python3
"""
Convert an image (PNG/BMP/JPG/etc.) to big-endian RGB565 (2 bytes/pixel, high byte first).

Usage:
  python img_to_rgb565be.py input.png
  python img_to_rgb565be.py input.jpg --rot 1
  python img_to_rgb565be.py input.bmp --rot 2 --out custom.bin

Rotation (--rot):
  0 = 0°   (no rotation)
  1 = 90°  clockwise
  2 = 180°
  3 = 270° clockwise
"""

from __future__ import annotations

import argparse
import os
import sys
from PIL import Image


_ROTATE_TRANSPOSE = {
    0: None,
    1: Image.Transpose.ROTATE_270,  # PIL uses counter-clockwise; 270° CCW = 90° CW
    2: Image.Transpose.ROTATE_180,
    3: Image.Transpose.ROTATE_90,   # 90° CCW = 270° CW
}


def image_to_rgb565_be_bytes(img: Image.Image) -> bytes:
    img = img.convert("RGB")
    w, h = img.size
    pixels = img.tobytes()  # RGBRGB...

    out = bytearray(w * h * 2)
    j = 0
    for i in range(0, len(pixels), 3):
        r = pixels[i]
        g = pixels[i + 1]
        b = pixels[i + 2]

        # RGB888 -> RGB565
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

        # Big-endian: high byte first
        out[j] = (rgb565 >> 8) & 0xFF
        out[j + 1] = rgb565 & 0xFF
        j += 2

    return bytes(out)


def derive_output_path(input_path: str) -> str:
    base, _ = os.path.splitext(input_path)
    return base + ".bin"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert an image to RGB565 big-endian raw bytes.")
    parser.add_argument("input", help="Input image file path (e.g. .png, .jpg, .bmp)")
    parser.add_argument(
        "--rot",
        type=int,
        default=0,
        choices=[0, 1, 2, 3],
        help="Rotation: 0=0°, 1=90° CW, 2=180°, 3=270° CW (default: 0)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output file path (default: same name as input with .bin extension)",
    )

    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        return 2

    out_path = args.out or derive_output_path(input_path)

    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"ERROR: Failed to open image: {e}", file=sys.stderr)
        return 3

    try:
        transpose_op = _ROTATE_TRANSPOSE[args.rot]
        if transpose_op is not None:
            img = img.transpose(transpose_op)

        data = image_to_rgb565_be_bytes(img)

        with open(out_path, "wb") as f:
            f.write(data)

        print(f"Wrote {len(data)} bytes to: {out_path}")
        return 0

    except Exception as e:
        print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
