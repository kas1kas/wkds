# woordklok v3.52
import argparse
import json
import logging
import time
import datetime
import os
import random
import bisect
#import math
import subprocess
from rpi_ws281x import PixelStrip, Color
from python_tsl2591 import tsl2591
from flask import Flask, request, render_template, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask app
app = Flask(__name__)

class WordClock:
    def __init__(self, config):
        self.release = config["RELEASE"]
        self.purist = config["PURIST"]
        self.language = config["LANGUAGE"]
        self.light_interval = config["LIGHT_INTERVAL"]
        self.led_count = config["LED_COUNT"]
        self.led_pin = config["LED_PIN"]
        self.led_freq_hz = config["LED_FREQ_HZ"]
        self.led_dma = config["LED_DMA"]
        self.led_channel = config["LED_CHANNEL"]
        self.background_color = config["BACKGROUND_COLOR"]
        self.letter_active_color = config["LETTER_ACTIVE_COLOR"]
        self.dot_inactive_color = config["DOT_INACTIVE_COLOR"]
        self.dot_active_color = config["DOT_ACTIVE_COLOR"]
        self.minute_dots = config["MINUTE_DOTS"]
        self.clock_type = config["CLOCK_TYPE"]
        self.cls_color = config["CLS_COLOR"]
        self.lut_in =  config.get("LUT_IN")
        self.lut_out=  config.get("LUT_OUT")
        self.CURSOR_UP = "\x1b[2A"
        self.minute_blocks = config["MINUTE_BLOCKS"].get(self.language,{})
        self.words = config["WORDS"].get(self.language,{})
        self.min_block_check = config["MIN_BLOCK_CHECK"].get(self.language,{})

        logging.info(f"Language: {self.language}") 
        # Initialize LED strip
        try:
            self.strip = PixelStrip(
                self.led_count, self.led_pin, self.led_freq_hz,
                self.led_dma, False, 100, self.led_channel
            )
            self.strip.begin()
            logging.info("LED strip initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize LED strip: {e}")
            exit(1)

        # Initialize TSL2591 light sensor
        try:
            self.light_sensor = tsl2591()
            logging.info("TSL2591 light sensor initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize TSL2591 light sensor: {e}")
            exit(1)

    #subs

    def wifi_connected(ssid=None):
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
                capture_output=True,
                text=True
            )
        
            # Parse output (format: "yes:MyWiFi\n")
            active_connections = [line.split(":") for line in result.stdout.strip().split("\n")]
        
            if ssid:
                # Check if a specific SSID is connected
                return any(active == "yes" and connected_ssid == ssid for active, connected_ssid in active_connections)
           else:
                # Check if any Wi-Fi is connected
                return any(active == "yes" for active, _ in active_connections)
    
        except Exception as e:
            print(f"Error checking Wi-Fi: {e}")
            return False
    
    def set_led_color(self, led_index, color):
         self.strip.setPixelColor(led_index, Color(color[0], color[1], color[2]))

    def map_grid_to_led(self, grid_index):
        if grid_index < 0 or grid_index > 109:
            return -1                          # Invalid index
        col = grid_index % 11                  # Column (0-10)
        row = grid_index // 11                 # Row (0-9, top to bottom)
        if col % 2 == 0:                       # Even columns: top to bottom
            return 2 + (col * 10) + row
        else:                                  # Odd columns: bottom to top
            return 2 + (col * 10) + (9 - row)

    def setcolor_x_y(self, x, y, b):
        if x < 0 or x > 10 or y < 0 or y > 9:
            return -1                          # Invalid coordinates
        if x % 2 == 0:                         # Even columns: top to bottom
            self.set_led_color(2 + (x * 10) + y, b)
        else:                                  # Odd columns: bottom to top
            self.set_led_color(2 + (x * 10) + (9 - y), b)

    def random_color(self):
      r = random.randint(  29, 69)   #  29, 69  shades of blue 
      g = random.randint(  31, 71)   #  31, 71
      b = random.randint(105,245)    # 105,245
      return (r, g, b)

    def kwheel(self, pos):
         if pos < 85:
            return (pos * 3, 255 - pos * 3, 0), Color(255-pos * 3, pos * 3, 255)
         elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3), Color(pos * 3, 255, 255-pos * 3)
         else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3), Color(255, 255-pos * 3, pos * 3)

    def set_random_led(self):
      self.set_led_color(random.randint(0,111), self.random_color())

    def cls(self):
        for i in range(self.led_count):
           self.set_led_color(i, self.background_color)

    def update_brightness(self):
      try:
          light_data = self.light_sensor.get_current()
          lux = abs(light_data['lux'])
      except Exception as e:
          logging.error(f"Failed to read light level: {e}")
          return
      index = bisect.bisect_right(self.lut_in, lux)
      brt = self.lut_out[index]
      self.strip.setBrightness(brt)

    def activate_word(self, word):
        if word in self.words:
            start, end = self.words[word]
            for i in range(start, end + 1):
                led_index = self.map_grid_to_led(i)
                if led_index != -1:
                    self.set_led_color(led_index, self.letter_active_color)

    def update_clock(self):
        """Update the clock display based on the current time."""
        now = time.localtime()
        hours = now.tm_hour % 12 or 12
        minutes = now.tm_min

       # Set minute dots
        minute_dots = minutes % 5
        for dot, index in self.minute_dots.items():
            self.set_led_color(index, self.dot_active_color \
                  if minute_dots >= list(self.minute_dots.keys()).index(dot) + 1 else self.dot_inactive_color)

        # Determine minute phrase and hour
        minute_block = minutes // 5
        adjusted_hours = hours

        # Show "HET IS"
        if not self.purist:
            if self.language == "NL":
              self.activate_word("HET")
            elif self.language == "EN":
              self.activate_word("IT")
            self.activate_word("IS")

        # Adjust hour starting at language determined minutes
        if minute_block >= self.min_block_check:
            adjusted_hours = (hours % 12) + 1
            if adjusted_hours == 13:
                adjusted_hours = 1

        # Activate words based on minute block
        if self.language == "NL":
            hour_words = ["EEN", "TWEE", "DRIE", "VIER", "VIJF2", "ZES", "ZEVEN", "ACHT", "NEGEN", "TIEN2", "ELF", "TWAALF"]
        elif self.language == "EN":
            hour_words = ["ONE", "TWO", "THREE", "FOUR", "FIVE2", "SIX", "SEVEN", "EIGHT", "NINE", "TEN2", "ELEVEN", "TWELVE"]

        if str(minute_block) in self.minute_blocks:
            for word in self.minute_blocks[str(minute_block)]:
                self.activate_word(word)
            self.activate_word(hour_words[adjusted_hours - 1])

        self.strip.show()

def load_config(config_file):
    """Load configuration from a JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print(f"Error: {config_file} not found at {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: {config_file} is not a valid JSON file.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Initialize word clock
# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run the Word Clock.")
parser.add_argument(
    "--release", 
    type=str, 
    default="3.5",  # Default value if --release is not provided
    help="Release version of the config file (e.g., 3). Default is '3.5'."
)
args = parser.parse_args()
# Use the provided release value
release = args.release

# ----------------------------------------Release is fixed here---------
config = load_config("config3.5.json")
word_clock = WordClock(config)

# Flask routes
@app.route("/")
def index():
    """Render the web interface with the initial settings."""
    initial_color = word_clock.letter_active_color
    initial_language = word_clock.language
    initial_clock_type = word_clock.clock_type
    initial_purist = word_clock.purist

    return render_template(
        "index.html",
        initial_color=initial_color,
        initial_language=initial_language,
        initial_clock_type=initial_clock_type,
        initial_purist=initial_purist
    )

@app.route("/set_color", methods=["POST"])
def set_color():
    """Set the color of the letters."""
    try:
        red = int(request.form.get("red"))
        green = int(request.form.get("green"))
        blue = int(request.form.get("blue"))

        word_clock.letter_active_color = (red, green, blue)

        return "Color updated successfully!", 200
    except Exception as e:
        logging.error(f"Failed to set color: {e}")
        return "Failed to update color.", 500

@app.route("/set_language", methods=["POST"])
def set_language():
    """Set the language of the word clock."""
    try:
        language = request.form.get("language")
        if language in ["NL", "EN"]:
            word_clock.language = language
            word_clock.words = config["WORDS"].get(language, {})
            word_clock.minute_blocks = config["MINUTE_BLOCKS"].get(language, {})
            word_clock.min_block_check = config["MIN_BLOCK_CHECK"].get(language, {})
            return "Language updated successfully!", 200
        else:
            return "Invalid language.", 400
    except Exception as e:
        logging.error(f"Failed to set language: {e}")
        return "Failed to update language.", 500

@app.route("/set_clock_type", methods=["POST"])
def set_clock_type():
    """Set the clock type."""
    try:
        clock_type = request.form.get("clock_type")
        if clock_type in ["regular", "random", "rainbow", "dark"]:
            word_clock.clock_type = clock_type
            return "Clock type updated successfully!", 200
        else:
            return "Invalid clock type.", 400
    except Exception as e:
        logging.error(f"Failed to set clock type: {e}")
        return "Failed to update clock type.", 500

@app.route("/set_purist", methods=["POST"])
def set_purist():
    """Set the purist mode."""
    try:
        purist = request.form.get("purist")
        if purist in ["true", "false"]:
            word_clock.purist = purist == "true"
            return "Purist mode updated successfully!", 200
        else:
            return "Invalid purist mode.", 400
    except Exception as e:
        logging.error(f"Failed to set purist mode: {e}")
        return "Failed to update purist mode.", 500

@app.route("/get_brightness", methods=["GET"])
def get_brightness():
    """Get the current brightness value."""
    try:
        light_data = word_clock.light_sensor.get_current()
        lux = round(abs(light_data['lux']),2)
        index = bisect.bisect_right(word_clock.lut_in, lux)
        brt = word_clock.lut_out[index]
        brightness_display = f"{lux}: {brt}"
        return jsonify({"brightness": brightness_display}), 200
    except Exception as e:
        logging.error(f"Failed to fetch brightness: {e}")
        return jsonify({"error": "Failed to fetch brightness"}), 500

# Main function to run the word clock
def run_clock():

    def onlyx(interval):
        if not hasattr(onlyx, "last_time"):
        # Initialize the last_time attribute if it doesn't exist
            onlyx.last_time = time.time() - interval  # Ensure it runs the first time
        current_time = time.time()
        if current_time - onlyx.last_time >= interval:
            onlyx.last_time = current_time
            return True
        return False

    """Run the word clock in a separate thread."""
    try:
      while True:
        if onlyx(3):
           word_clock.update_brightness()

        if word_clock.clock_type == "regular":
           word_clock.cls()

        if word_clock.clock_type == "dark":
           word_clock.cls()
           word_clock.strip.show()
           time.sleep(1)

        elif word_clock.clock_type == "random":
           a = random.randint(0,word_clock.led_count)
           b = word_clock.random_color()
           word_clock.set_led_color(a,b)

        elif word_clock.clock_type == "rainbow":
           for j in range(256 * 5):
               for x in range(11):          #width()):
                   for y in range(10):      #height()):
                      k=(x * y + j) & 255
                      b,w = word_clock.kwheel(k)
                      word_clock.setcolor_x_y(x,y,b)
               word_clock.update_clock()
               time.sleep(0.01)

        if word_clock.clock_type != "dark":
          word_clock.update_clock()
    except KeyboardInterrupt:
        logging.info("Exiting...")
    finally:
        # Clean up on exit
        for i in range(word_clock.led_count):
            word_clock.set_led_color(i, word_clock.background_color)
        word_clock.strip.show()

if __name__ == "__main__":
    # Start the Flask web server in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=80))
    flask_thread.daemon = True
    flask_thread.start()

    # Run the word clock
    run_clock()
