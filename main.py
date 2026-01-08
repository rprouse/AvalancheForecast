import urequests

from time import sleep
from wifi import wifi_connect
from ili9341 import Display, color565
from machine import Pin, SPI  # type: ignore
from xglcd_font import XglcdFont

def run_font_demo():
    print('Starting font demo...')
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

    display = Display(spi, dc=Pin(TFT_DC_PIN), cs=Pin(TFT_CS_PIN), rst=Pin(TFT_RST_PIN), rotation=180)

    print('Loading fonts...')
    print('Loading arcadepix')
    arcadepix = XglcdFont('ArcadePix9x11.c', 9, 11)

    print('Loading bally')
    bally = XglcdFont('Bally7x9.c', 7, 9)

    print('Loading dejavu')
    dejavu = XglcdFont('Dejavu24x43.c', 24, 43)

    print('Loading fixed_font')
    fixed_font = XglcdFont('FixedFont5x8.c', 5, 8)

    print('Loading unispace')
    unispace = XglcdFont('Unispace12x24.c', 12, 24)

    print('Loading wendy')
    wendy = XglcdFont('Wendy7x8.c', 7, 8)

    print('Fonts loaded.')

    text_heights = [11, 9, 43, 8, 24, 24, 8]  # Heights of each line
    num_lines = len(text_heights)  # Number of lines
    total_text_height = sum(text_heights)  # Total height of all text lines
    # Calculate available space to distribute
    available_height = display.height - total_text_height
    # Calculate the vertical gap between each line
    gap_between_lines = available_height // (num_lines + 1)
    # Start drawing the text at the first position

    display.clear()

    # Calculate available horizontal space
    available_width = display.width - total_text_height
    # Calculate the horizontal gap between each line
    gap_between_lines = available_width // (num_lines + 1)
    # Starting X position for each line
    x_position = gap_between_lines
    # Draw each text line with adjusted X positions
    display.draw_text(x_position, display.height - 1, 'Arcade Pix 9x11',
                      arcadepix, color565(255, 0, 0), landscape=True)
    x_position += text_heights[0] + gap_between_lines
    display.draw_text(x_position, display.height - 1, 'Bally 7x9', bally,
                      color565(0, 255, 0), landscape=True)
    x_position += text_heights[1] + gap_between_lines
    display.draw_text(x_position, display.height - 1, 'Dejavu 24x43',
                      dejavu, color565(0, 0, 255), landscape=True)
    x_position += text_heights[2] + gap_between_lines
    x_position += text_heights[3] + gap_between_lines
    display.draw_text(x_position, display.height - 1, 'Fixed Font 5x8',
                      fixed_font, color565(255, 0, 255), landscape=True)
    x_position += text_heights[4] + gap_between_lines
    display.draw_text(x_position, display.height - 1, 'Unispace 12x24',
                      unispace, color565(255, 128, 0), landscape=True)
    x_position += text_heights[5] + gap_between_lines
    display.draw_text(x_position, display.height - 1, 'Wendy 7x8', wendy,
                      color565(255, 0, 128), landscape=True)

wlan = wifi_connect()

# Fetch avalanche forecast data from the Avalanche Canada API
response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
print("Response status:", response.status_code)

if response.status_code == 200:
    data = response.json()
    title = data['report']['title']
    print("Report title:", title)
    print()

    # Display danger ratings
    for danger_rating in data['report']['dangerRatings']:
        print(danger_rating['date']['display'])
        ratings = danger_rating['ratings']
        print("  " + ratings['alp']['display'] + ": " + ratings['alp']['rating']['display'])
        print("  " + ratings['tln']['display'] + ": " + ratings['tln']['rating']['display'])
        print("  " + ratings['btl']['display'] + ": " + ratings['btl']['rating']['display'])
        print()
else:
    print("Failed to fetch forecast data")

run_font_demo()
