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

The code for driving the [ILI9341(https://www.lcdwiki.com/2.8inch_SPI_Module_ILI9341_SKU%3AMSP2807)] Touch Display is from [rdagger/micropython_ili9341](https://github.com/rdagger/micropython-ili9341).

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
