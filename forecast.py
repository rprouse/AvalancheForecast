import colors
import fonts.tt7, fonts.tt14

class AvalancheForecast:
    ...
    def __init__(self, tft) -> None:
        self.tft = tft

    def get_forecast(self, lat: float, long: float) -> dict:
        """
        Fetch the avalanche forecast data for the specified latitude and longitude.

        Parameters:
            lat (float): Latitude of the location.
            long (float): Longitude of the location.
        Returns:
            dict: Parsed JSON response containing the forecast data.
        """
        import urequests

        url = f"https://api.avalanche.ca/forecasts/en/products/point?lat={lat}&long={long}"
        response = urequests.get(url)
        if response.status_code == 200:
            data = response.json()
            response.close()
            return data
        else:
            response.close()
            raise Exception(f"Failed to fetch forecast data: HTTP {response.status_code}")

    def _display_day_forecast(self, today: dict, y: int) -> int:
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
        self.tft.set_font(fonts.tt14)
        self.tft.text(today['date']['display'], 10, y, colors.GRAY)
        self.tft.set_font(fonts.tt7)

        y = y + 18
        rating = today['ratings']['alp']['rating']['value']
        bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
        fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
        self.tft.fill_rect(10, y, 100, 16, colors.ALP)
        self.tft.text("Alpine", 14, y + 4, colors.BLACK)
        self.tft.fill_rect(112, y, 100, 16, bg_color)
        self.tft.text(today['ratings']['alp']['rating']['display'], 116,  y + 4, fg_color)
        y = y + 18
        rating = today['ratings']['tln']['rating']['value']
        bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
        fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
        self.tft.fill_rect(10, y, 100, 16, colors.TLN)
        self.tft.text("Treeline", 14, y + 4, colors.BLACK)
        self.tft.fill_rect(112, y, 100, 16, bg_color)
        self.tft.text(today['ratings']['tln']['rating']['display'], 116,  y + 4, fg_color)

        y = y + 18
        rating = today['ratings']['btl']['rating']['value']
        bg_color = colors.DANGER_BG_COLORS.get(rating, colors.GRAY)
        fg_color = colors.DANGER_FG_COLORS.get(rating, colors.BLACK)
        self.tft.fill_rect(10, y, 100, 16, colors.BTL)
        self.tft.text("Below Treeline", 14, y + 4, colors.BLACK)
        self.tft.fill_rect(112, y, 100, 16, bg_color)
        self.tft.text(today['ratings']['btl']['rating']['display'], 116,  y + 4, fg_color)
        return y + 24

    def display_forecast(self, data: dict, y: int) -> int:
        """
        Render the full avalanche forecast onto the provided TFT display and return the next
        vertical drawing position.
        Parameters:
            tft: TFT display instance used for drawing (must support text, set_font, fill_rect).
            data (dict): Full forecast data as returned by get_forecast().
            y (int): Starting vertical pixel coordinate for rendering.
        Returns:
            int: The vertical pixel coordinate to continue drawing after this block.
        """
        for danger_rating in data['report']['dangerRatings']:
            print("Danger rating:", danger_rating)
            y = self._display_day_forecast(danger_rating, y)
        return y
