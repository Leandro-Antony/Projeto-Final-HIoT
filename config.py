import json

def save_config(config):
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)

def load_config():
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {
            "gpu": {
                "vendor": None
            }
        }
    return config