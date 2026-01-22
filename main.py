from machine import Pin, RTC, SPI
import ntptime
import urequests
import os

import colors
from drivers.tft_spi import ILI9341, color565
import fonts.tt7, fonts.tt14, fonts.tt24, fonts.tt32
from drivers.xpt2046 import Touch
import pins
from secrets import SSID, PASSWORD
import wifi

SCR_WIDTH = const(240)
SCR_HEIGHT = const(360)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

def initialize_display():
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
    tft.fill(colors.BLACK)
    return tft

# --- NTP sync ---
def sync_time():
    """Synchronize the device's RTC with an NTP server."""
    # Canadian NTP pool
    ntptime.host = "ca.pool.ntp.org"
    ntptime.settime()  # sets RTC to UTC

def display_forecast(tft, today, y):
    """
    Render the forecast date and three danger-rating rows (Alpine, Treeline, Below
    Treeline) onto the provided TFT display and return the next vertical drawing position.

    Parameters:
        tft: TFT display instance used for drawing (must support text, set_font, fill_rect).
        today (dict): Forecast data for a single day; expected to contain 'date'->'display'
        and 'ratings'->{'alp','tln','btl'} with each having 'rating'->{'value','display'}.
        y (int): Starting vertical pixel coordinate for rendering.

    Returns:
        int: The vertical pixel coordinate to continue drawing after this block.
    """
    tft.set_font(fonts.tt14)
    tft.text(today['date']['display'], 10, y, colors.GRAY)
    tft.set_font(fonts.tt7)

    y = y + 18
    rating = today['ratings']['alp']['rating']['value']
    bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
    fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
    tft.fill_rect(10, y, 100, 16, colors.ALP)
    tft.text("Alpine", 14, y + 4, colors.BLACK)
    tft.fill_rect(112, y, 100, 16, bg_color)
    tft.text(today['ratings']['alp']['rating']['display'], 116,  y + 4, fg_color)

    y = y + 18
    rating = today['ratings']['tln']['rating']['value']
    bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
    fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
    tft.fill_rect(10, y, 100, 16, colors.TLN)
    tft.text("Treeline", 14, y + 4, colors.BLACK)
    tft.fill_rect(112, y, 100, 16, bg_color)
    tft.text(today['ratings']['tln']['rating']['display'], 116,  y + 4, fg_color)

    y = y + 18
    rating = today['ratings']['btl']['rating']['value']
    bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
    fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
    tft.fill_rect(10, y, 100, 16, colors.BTL)
    tft.text("Below Treeline", 14, y + 4, colors.BLACK)
    tft.fill_rect(112, y, 100, 16, bg_color)
    tft.text(today['ratings']['btl']['rating']['display'], 116,  y + 4, fg_color)

    return y + 24


def touchscreen_press(x, y):
    """Process touchscreen press events."""
    # Y needs to be flipped
    x = (SCR_WIDTH - 1) - x
    print(f"Touch at x={x}, y={y}")

def main():
    print(os.uname()) # type: ignore
    tft = initialize_display()

    print("Initializing Touch...")
    spi2 = SPI(1, baudrate=1000000, sck=Pin(pins.TOUCH_CLK_PIN), mosi=Pin(pins.TOUCH_MOSI_PIN), miso=Pin(pins.TOUCH_MISO_PIN))
    # The Pico Breadboard Kit does not have the interrupt pin connected, so we
    # won't use it here, instead we will poll for touches
    touch = Touch(spi2, cs=Pin(pins.TOUCH_CS_PIN))# , int_pin=Pin(pins.TOUCH_INT_PIN)), int_handler=touchscreen_press)

    print("Connecting to WiFi...")
    tft.text("Connecting to WiFi...", 10, 10, colors.GREEN)

    wlan = wifi.connect(SSID, PASSWORD, timeout_s=20, country="CA", verbose=True)

    # Setting device time
    print("Setting device time via NTP...")
    tft.text("Setting device time via NTP...", 10, 22, colors.GREEN)
    sync_time()

    rtc = RTC()

    # RTC returns (year, month, day, weekday, hour, minute, second, subseconds)
    t = rtc.datetime()
    ts = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} UTC".format(t[0], t[1], t[2], t[4], t[5], t[6])
    print(ts)
    tft.text(ts, 10, 34, colors.GREEN)
    # Fetch avalanche forecast data from the Avalanche Canada API
    print("Getting Avalanche Forecast...")
    tft.text("Getting Avalanche Forecast...", 10, 46, colors.GREEN)

    response = None
    try:
        response = urequests.get("https://api.avalanche.ca/forecasts/en/products/point?lat=49.516324&long=-115.068756")
        tft.fill(colors.BLACK)
        print("Response status:", response.status_code)
        if response.status_code == 200:
            print("Parsing forecast data...")
            data = response.json()
            title = data['report']['title']
            # display.set_font(tt14)
            # display.set_color(color565(0, 255, 255), color565(0, 0, 0))
            # display.print(title + "\n")

            # Display danger ratings
            y = 10
            for danger_rating in data['report']['dangerRatings']:
                print("Danger rating:", danger_rating)
                y = display_forecast(tft, danger_rating, y)

        else:
            tft.set_font(fonts.tt7)
            tft.text("Failed to fetch forecast data", 10, 10, colors.WHITE)

        print("Entering touch event loop.  Press Ctrl-C to exit.")
        while True:
            # Re-sync occasionally to limit drift (e.g. once per hour)
            t = rtc.datetime()
            if t[5] == 0 and t[6] < 2:  # near top of the hour
                try:
                    sync_time()
                    print("NTP re-sync OK")
                except Exception as e:
                    print("NTP re-sync failed:", e)

            # Check for touch events
            result = touch.get_touch()
            if result is not None:
                x, y = touch.normalize(*result)
                touchscreen_press(x, y)

    except KeyboardInterrupt:
        print("\nCtrl-C pressed.  Cleaning up and exiting...")
        return

    except Exception as e:
        # Handle network or parsing errors
        print("Error fetching forecast data:", e)
        tft.set_font(fonts.tt7)
        tft.text("Error fetching forecast data", 10, 10, colors.WHITE)

    finally:
        if response is not None:
            response.close()

        if tft is not None:
            tft.fill(colors.BLACK)
            tft.text("Done.", 10, 10, colors.GREEN)

if __name__ == "__main__":
    main()
