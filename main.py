import colors
import display
import fonts.tt7
import ntptime
import os
import pins
import wifi

from drivers.xpt2046 import Touch
from forecast import AvalancheForecast
from machine import Pin, RTC, SPI
from secrets import SSID, PASSWORD

class AvalancheForecastApplication:
    def __init__(self):
        print(os.uname()) # type: ignore
        self.tft = display.initialize()

        self.y = 10 # Initial vertical position for drawing

        print("Initializing Touch...")
        self.spi2 = SPI(1, baudrate=1000000, sck=Pin(pins.TOUCH_CLK_PIN), mosi=Pin(pins.TOUCH_MOSI_PIN), miso=Pin(pins.TOUCH_MISO_PIN))
        # The Pico Breadboard Kit does not have the interrupt pin connected, so we
        # won't use it here, instead we will poll for touches
        self.touch = Touch(self.spi2, cs=Pin(pins.TOUCH_CS_PIN))# , int_pin=Pin(pins.TOUCH_INT_PIN)), int_handler=touchscreen_press)

        print("Connecting to WiFi...")
        self.y = self.tft.text("Connecting to WiFi...", 10, self.y, colors.GREEN)

        wlan = wifi.connect(SSID, PASSWORD, timeout_s=20, country="CA", verbose=True)

        # Setting device time
        print("Setting device time via NTP...")
        self.y = self.tft.text("Setting device time via NTP...", 10, self.y, colors.GREEN)
        self.sync_time()

        self.rtc = RTC()

        # RTC returns (year, month, day, weekday, hour, minute, second, subseconds)
        t = self.rtc.datetime()
        ts = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} UTC".format(t[0], t[1], t[2], t[4], t[5], t[6])
        print(ts)
        self.y = self.tft.text(ts, 10, self.y, colors.GREEN)
        self.forecast = AvalancheForecast(self.tft)

    # --- NTP sync ---
    def _sync_time(self):
        """Synchronize the device's RTC with an NTP server."""
        # Canadian NTP pool
        ntptime.host = "ca.pool.ntp.org"
        ntptime.settime()  # sets RTC to UTC

    def _touchscreen_press(self, x, y):
        """Process touchscreen press events."""
        # Y needs to be flipped
        x = (display.SCR_WIDTH - 1) - x
        print(f"Touch at x={x}, y={y}")

    def get_forecast(self):
        # Fetch avalanche forecast data from the Avalanche Canada API
        print("Getting Avalanche Forecast...")
        self.y = self.tft.text("Getting Avalanche Forecast...", 10, self.y, colors.GREEN)

        self.data = self.forecast.get_forecast(49.516324, -115.068756)  # Example: Fernie, BC
        self.tft.erase()

        print("Parsing forecast data...")
        self.title = self.data['report']['title']
        # display.set_font(tt14)
        # display.set_color(color565(0, 255, 255), color565(0, 0, 0))
        # display.print(title + "\n")

        # Display danger ratings
        self.y = 10;
        self.y = self.forecast.display_forecast(self.data, self.y)

    def run(self):
        try:
            print("Entering event loop.  Press Ctrl-C to exit.")
            while True:
                # Re-sync occasionally to limit drift (e.g. once per hour)
                t = self.rtc.datetime()
                if t[5] == 0 and t[6] < 2:  # near top of the hour
                    try:
                        self._sync_time()
                        print("NTP re-sync OK")
                    except Exception as e:
                        print("NTP re-sync failed:", e)

                # Check for touch events
                result = self.touch.get_touch()
                if result is not None:
                    x, y = self.touch.normalize(*result)
                    self._touchscreen_press(x, y)
        except KeyboardInterrupt:
            print("\nCtrl-C pressed.  Cleaning up and exiting...")
            if self.tft is not None:
                self.tft.erase()
                self.y = self.tft.text("Done.", 10, 10, colors.GREEN)
            return

    def error(self, msg: str):
        """Display an error message on the TFT display and the console."""
        print("Error:", msg)
        self.tft.erase()
        self.tft.set_font(fonts.tt7)
        self.y = self.tft.text(msg, 10, 10, colors.RED)

def main():
    try:
        app = AvalancheForecastApplication()
        app.get_forecast()
        app.run()
    except Exception as e:
        # Handle network or parsing errors
        app.error(str(e))

if __name__ == "__main__":
    main()
