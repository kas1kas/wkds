#v12.3
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
    config =load_config("config3.2.json") 
    woordklok = config.get("WOORDKLOK")
    inval =  config.get("LUT_IN").get(woordklok,{})
    uitval=  config.get("LUT_OUT").get(woordklok,{})
    logging.info(f"woordklok:{woordklok}")
    tsl = tsl2591()  # initialize

    in_str =  ", ".join(f"{x:>4}" for x in inval)
    out_str = ", ".join(f"{x:>4}" for x in uitval)
    print(f"In : {in_str}")
    print(f"Out: {out_str}")
    print("----------------------------------------")

    while True:
        lux = readlux()
        newbright = lut(lux)

        logging.info(f"L: {lux}   B: {newbright}")

