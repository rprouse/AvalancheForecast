import urequests

from wifi import wifi_connect
from ili9341 import color565
from display import initialize_display, load_display_fonts

def run_font_demo():
    display = initialize_display()
    fonts = load_display_fonts()

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
    display.draw_text(x_position, display.height - 1, 'Arcade Pix 9x11', fonts[0], color565(255, 0, 0), landscape=True)
    x_position += text_heights[0] + gap_between_lines

    display.draw_text(x_position, display.height - 1, 'Bally 7x9', fonts[1], color565(0, 255, 0), landscape=True)
    x_position += text_heights[1] + gap_between_lines

    display.draw_text(x_position, display.height - 1, 'Dejavu 24x43', fonts[2], color565(0, 0, 255), landscape=True)
    x_position += text_heights[2] + gap_between_lines

    display.draw_text(x_position, display.height - 1, 'Fixed Font 5x8', fonts[3], color565(255, 0, 255), landscape=True)
    x_position += text_heights[3] + gap_between_lines

    display.draw_text(x_position, display.height - 1, 'Unispace 12x24', fonts[4], color565(255, 128, 0), landscape=True)
    x_position += text_heights[4] + gap_between_lines

    display.draw_text(x_position, display.height - 1, 'Wendy 7x8', fonts[5], color565(255, 0, 128), landscape=True)

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
