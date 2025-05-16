#v3.5 compatible
from python_tsl2591 import tsl2591
import sys
import bisect
import argparse
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def bargraph(s, p, r):
    return s[:p] + r + s[p+1:]

def readlux():
    full, ir = tsl.get_full_luminosity()
    return max(0, (tsl.calculate_lux(full, ir)))

def lut(lux):
    index = bisect.bisect_right(inval, lux)
    return uitval[index]

def load_config(config_file):
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


if __name__ == '__main__':
    config =load_config("config3.5.json") 
    inval =  config.get("LUT_IN")
    uitval=  config.get("LUT_OUT")
    logging.info(f"in :{inval}")
    logging.info(f"uit:{uitval}")
    lineaal = "├───┴───┴───┴───┴───┼───┴───┴───┴───┴───┤"
    luxmax = 200
    brtmax = 250
    luxscalemax = 40
    brtscalemax = 40
    CURSOR_UP = "\x1b[2A"
    tsl = tsl2591()  # initialize

    in_str =  ", ".join(f"{x:>4}" for x in inval)
    out_str = ", ".join(f"{x:>4}" for x in uitval)
    print(f"In : {in_str}")
    print(f"Out: {out_str}")
    print("----------------------------------------")

    while True:
        lux = readlux()
        newbright = lut(lux)
        x = int(lux * (luxscalemax / luxmax))
        y = int(newbright * (brtscalemax / brtmax))
        graphlux = bargraph(lineaal, x, "■")
        graphbrt = bargraph(lineaal, y, "■")

        format_str = (
            "%5.0f" if lux >= 100 else  # No decimals for 100-999
            "%5.1f" if lux >= 10 else   # 1 decimal for 10-99
            "%5.2f" if lux >= 1 else    # 2 decimals for 1-9
            "%5.3f"                    # 3 decimals for < 1
        )

        formatted_lux = format_str % lux

        if lux < 1 and formatted_lux.startswith("0"):
           formatted_lux = formatted_lux[1:]

        print("L: " + formatted_lux, end="")
#        print("L: %5.1f" % lux, end="")
        print(graphlux, luxmax, " ")

        print("B: %5d" % newbright, end="")
        print(graphbrt, brtmax)

        sys.stdout.write(CURSOR_UP)
