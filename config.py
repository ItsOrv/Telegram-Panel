import json
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

API_ID = load_config()['api_id']
API_HASH = load_config()['api_hash']
BOT_TOKEN = load_config()['bot_token']
