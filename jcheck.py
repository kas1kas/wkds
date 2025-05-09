import json
with open("config.json", "r") as f:
    try:
        json.load(f)
        print("Valid JSON")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
