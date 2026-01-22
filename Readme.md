# Fernie Avalanche Forecast

## Avalanche Canada API

Avalanche Canada provides a public API and provides [API Documentation](https://docs.avalanche.ca/).

[Graphic Assets](https://github.com/avalanche-canada/ac-assets) and the [Avalanche forecast subregions](https://github.com/avalanche-canada/forecast-polygons) are published on GitHub.

## WiFi Configuration

You must create a `secrets.py` file with your WiFi SSID and PASSWORD.

```py
SSID = ""
PASSWORD = ""
```

## ILI9341 Display

The code for driving multiple touch displays like,

- [320x240 2.8" SPI Module ILI9341](https://www.lcdwiki.com/2.8inch_SPI_Module_ILI9341_SKU%3AMSP2807)
- Possibly the [480x320 3.5" SPI Module ILI9488](https://www.lcdwiki.com/3.5inch_SPI_Module_ILI9488_SKU%3AMSP3520)
- And the [480x320 4.0" SPI Module ST7796](https://www.lcdwiki.com/4.0inch_SPI_Module_ST7796)

I am using the following pins based on the [Pico Breadboard Kit](https://wiki.52pi.com/index.php?title=EP-0164) with [Example Code](https://github.com/geeekpi/picoBDK). I may switch to their driver.

| SPI         | Pin |
| ----------- | --- |
| SCK/CLK     |   6 |
| MOSI/SDI/TX |   7 |
| MISO/SDO    |   4 |
| CS          |  13 |
| RST         |  14 |
| DC          |  15 |

The touch screen uses the following pins,

| SPI         | Pin |
| ----------- | --- |
| SCK/CLK     |  10 |
| MOSI/SDI/TX |  11 |
| MISO/SDO    |   8 |
| CS          |  12 |

![Pinout Details](https://github.com/geeekpi/picoBDK/raw/main/imgs/Pinout.jpg)
