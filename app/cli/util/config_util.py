import json
import os

CONFIG_FILE = "config.json"


def load_config():
    """Load config.json safely. Returns dict or {} if missing/corrupted."""
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # corrupted JSON fallback
        return {}


def save_config(data):
    """Write given dictionary to config.json safely."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to save config: {e}")


def save_token(token):
    """Save JWT token into config.json."""
    config = load_config()
    config["token"] = token
    save_config(config)


def load_token():
    """Load JWT token from config.json."""
    config = load_config()
    return config.get("token")


def clear_token():
    """Remove JWT token from config.json."""
    config = load_config()
    if "token" in config:
        del config["token"]
        save_config(config)
