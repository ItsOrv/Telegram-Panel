import json
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading JSON: {e}")
        return None
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        return None


config = load_config()

if config:
    API_ID = config['api_id']
    API_HASH = config['api_hash']
    BOT_TOKEN = config['bot_token']
else:
    raise ValueError("Failed to load configuration.")
