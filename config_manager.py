import json
import os
from typing import Dict, Any

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}")
            self._config = {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file at {config_path}")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'websocket.port')"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_websocket_url(self) -> str:
        """Get the WebSocket URL from config"""
        host = self.get('websocket.host', '127.0.0.1')
        port = self.get('websocket.port', 8766)
        return f"ws://{host}:{port}"

# Create a singleton instance
config = ConfigManager() 