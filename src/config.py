import os
import json
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ConfigManager:
    def __init__(self, filename: str = "config.json", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ConfigManager with a default configuration or load it from a file.
        :param filename: Path to the configuration file.
        :param config: Initial configuration dictionary (optional).
        """
        self.filename = filename
        self.default_config = {
            "TARGET_GROUPS": [],
            "KEYWORDS": [],
            "IGNORE_USERS": [],
            "clients": []
        }
        self.config = config if config else self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the JSON file or return the default configuration if the file doesn't exist or is invalid.
        :return: Loaded configuration dictionary.
        """
        if not os.path.exists(self.filename) or os.path.getsize(self.filename) == 0:
            logger.warning(f"Config file '{self.filename}' not found or it's empty. Creating a new one with default settings.")
            self.save_config(self.default_config)
            return self.default_config.copy()

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                if not isinstance(loaded_config, dict):
                    raise ValueError("Config file must contain a JSON object")
                logger.info("Config file loaded successfully.")
                return {**self.default_config, **loaded_config}
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.error(f"Error loading config file '{self.filename}': {e}. Falling back to default config.")
            return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save the configuration to the JSON file.
        :param config: Configuration dictionary to save.
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info("Configuration saved successfully.")
        except OSError as e:
            logger.error(f"Failed to save config file '{self.filename}': {e}")

    def update_config(self, key: str, value: Any) -> None:
        """
        Update a specific configuration key with a new value and save the changes.
        :param key: Configuration key to update.
        :param value: New value for the key.
        """
        if key not in self.default_config:
            logger.warning(f"Key '{key}' not found in default configuration. Adding it.")
        elif self.config is None:
            raise ValueError("Config is not initialized")
        self.config[key] = value
        self.save_config()

    def merge_config(self, new_config: Dict[str, Any]) -> None:
        """
        Merge a new configuration dictionary with the current configuration.
        :param new_config: Dictionary containing configuration updates.
        """
        for key, value in new_config.items():
            if key in self.config and isinstance(self.config[key], list) and isinstance(value, list):
                self.config[key] = list(set(self.config[key] + value))
            else:
                self.config[key] = value
        self.save_config()

    def get_config(self, key: Optional[str] = None) -> Union[Dict[str, Any], Any]:
        """
        Retrieve the entire configuration or the value of a specific key.
        :param key: Configuration key to retrieve (optional).
        :return: Configuration value or the entire configuration dictionary.
        """
        if key is None:
            return self.config
        return self.config.get(key, None)

# Load environment variables
load_dotenv()
def get_env_variable(name: str, default: Optional[Any] = None) -> Any:
    """
    Retrieve an environment variable with an optional default value.
    :param name: Name of the environment variable.
    :param default: Default value if the environment variable is not set.
    :return: Environment variable value or default.
    """
    value = os.getenv(name)
    if value is None:
        logger.warning(f"Environment variable '{name}' not found. Please add it to .env file. Using default value: {default}")
        return default
    return value

# Required configuration values
API_ID = get_env_variable('API_ID', default=0)
API_HASH = get_env_variable('API_HASH', default='x')
BOT_TOKEN = get_env_variable('BOT_TOKEN', default='x')
CHANNEL_ID = get_env_variable('CHANNEL_ID', default='x')
BOT_SESSION_NAME = get_env_variable('BOT_SESSION_NAME', default='BOT_SESSION')
ADMIN_ID = get_env_variable('ADMIN_ID', default=0)



