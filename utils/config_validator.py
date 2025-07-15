"""
Configuration validation utility for Aiayer
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration files and provides default values"""
    
    REQUIRED_SECTIONS = [
        'system', 'sensors', 'llm', 'memory', 'logging'
    ]
    
    DEFAULT_CONFIG = {
        'system': {
            'name': 'Local AI Assistant',
            'version': '0.1.0',
            'debug': False
        },
        'agent': {
            'filter_patterns': [
                'password', 'secret', 'key', 'token', 'api_key',
                'private_key', 'ssh_key', 'credential', 'authentication',
                'authorization'
            ]
        },
        'sensors': {
            'screen': {
                'enabled': True,
                'interval_sec': 10,
                'capture_active_window_only': True,
                'ocr_language': 'eng',
                'max_text_length': 3000
            },
            'file': {
                'enabled': True,
                'paths': [],
                'ignore_patterns': [
                    '*.tmp', '~*', '.DS_Store', 'Thumbs.db', '.git/*',
                    '__pycache__/*', 'node_modules/*', '*.pyc', '*.pyo', '*.log'
                ],
                'max_events': 50
            },
            'process': {
                'enabled': True,
                'interval_sec': 5,
                'track_all_processes': False,
                'check_interval': 5
            },
            'browser': {
                'enabled': True,
                'check_interval': 5
            }
        },
        'llm': {
            'model_name': 'mistral:latest',
            'host': 'localhost',
            'port': 11434,
            'request_timeout_sec': 60,
            'temperature': 0.7,
            'max_tokens': 1000,
            'top_p': 0.95,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'retry_attempts': 2
        },
        'memory': {
            'max_conversation_length': 20,
            'max_token_budget': 50,
            'store_timestamps': False
        },
        'overlay': {
            'enabled': True,
            'websocket_port': 8765,
            'window': {
                'width': 800,
                'height': 600,
                'transparent': True,
                'always_on_top': True,
                'decorations': False
            },
            'tauri': {
                'dev_mode': True
            },
            'overlay_path': 'overlay',
            'check_interval': 5
        },
        'security': {
            'sensitivity_patterns_path': 'config/sensitivity_patterns.txt',
            'allow_read_file_content': True,
            'allow_network_access': False,
            'sanitize_sensitive_data': True,
            'bind_to_localhost': True
        },
        'ui': {
            'host': '127.0.0.1',
            'port': 5001,
            'title': 'Local AI Assistant',
            'theme': 'auto',
            'enable_markdown': True
        },
        'logging': {
            'level': 'INFO',
            'file': 'aiayer.log',
            'max_size_mb': 10,
            'backup_count': 3,
            'log_to_console': True
        }
    }
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.errors = []
        self.warnings = []
    
    def validate(self) -> bool:
        """Validate the configuration file"""
        self.errors = []
        self.warnings = []
        
        try:
            # Load configuration
            if not self.load_config():
                return False
            
            # Validate required sections
            self._validate_required_sections()
            
            # Validate individual sections
            self._validate_system_section()
            self._validate_sensors_section()
            self._validate_llm_section()
            self._validate_memory_section()
            self._validate_logging_section()
            self._validate_security_section()
            self._validate_ui_section()
            
            # Validate paths
            self._validate_paths()
            
            # Report results
            if self.errors:
                logger.error(f"Configuration validation failed with {len(self.errors)} errors:")
                for error in self.errors:
                    logger.error(f"  - {error}")
                return False
            
            if self.warnings:
                logger.warning(f"Configuration validation completed with {len(self.warnings)} warnings:")
                for warning in self.warnings:
                    logger.warning(f"  - {warning}")
            
            logger.info("Configuration validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"Configuration file not found: {self.config_path}")
                return False
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            if not self.config:
                logger.error("Configuration file is empty")
                return False
            
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in configuration file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def _validate_required_sections(self):
        """Validate that all required sections are present"""
        for section in self.REQUIRED_SECTIONS:
            if section not in self.config:
                self.errors.append(f"Missing required section: {section}")
    
    def _validate_system_section(self):
        """Validate system section"""
        if 'system' not in self.config:
            return
        
        system = self.config['system']
        required_fields = ['name', 'version']
        
        for field in required_fields:
            if field not in system:
                self.errors.append(f"Missing required field in system section: {field}")
        
        if 'debug' in system and not isinstance(system['debug'], bool):
            self.errors.append("System debug field must be a boolean")
    
    def _validate_sensors_section(self):
        """Validate sensors section"""
        if 'sensors' not in self.config:
            return
        
        sensors = self.config['sensors']
        sensor_types = ['screen', 'file', 'process', 'browser']
        
        for sensor_type in sensor_types:
            if sensor_type in sensors:
                self._validate_sensor_config(sensor_type, sensors[sensor_type])
    
    def _validate_sensor_config(self, sensor_type: str, config: Dict[str, Any]):
        """Validate individual sensor configuration"""
        if 'enabled' in config and not isinstance(config['enabled'], bool):
            self.errors.append(f"{sensor_type} sensor enabled field must be a boolean")
        
        if sensor_type == 'screen':
            if 'interval_sec' in config and not isinstance(config['interval_sec'], (int, float)):
                self.errors.append("Screen sensor interval_sec must be a number")
            if 'interval_sec' in config and config['interval_sec'] < 1:
                self.warnings.append("Screen sensor interval is very short, may impact performance")
        
        elif sensor_type == 'file':
            if 'paths' in config and not isinstance(config['paths'], list):
                self.errors.append("File sensor paths must be a list")
            if 'paths' in config:
                for path in config['paths']:
                    if not os.path.exists(path):
                        self.warnings.append(f"File sensor path does not exist: {path}")
        
        elif sensor_type == 'process':
            if 'interval_sec' in config and not isinstance(config['interval_sec'], (int, float)):
                self.errors.append("Process sensor interval_sec must be a number")
    
    def _validate_llm_section(self):
        """Validate LLM section"""
        if 'llm' not in self.config:
            return
        
        llm = self.config['llm']
        required_fields = ['model_name', 'host', 'port']
        
        for field in required_fields:
            if field not in llm:
                self.errors.append(f"Missing required field in LLM section: {field}")
        
        if 'port' in llm and not isinstance(llm['port'], int):
            self.errors.append("LLM port must be an integer")
        
        if 'temperature' in llm and not isinstance(llm['temperature'], (int, float)):
            self.errors.append("LLM temperature must be a number")
        
        if 'temperature' in llm and (llm['temperature'] < 0 or llm['temperature'] > 2):
            self.warnings.append("LLM temperature should be between 0 and 2")
    
    def _validate_memory_section(self):
        """Validate memory section"""
        if 'memory' not in self.config:
            return
        
        memory = self.config['memory']
        
        if 'max_conversation_length' in memory and not isinstance(memory['max_conversation_length'], int):
            self.errors.append("Memory max_conversation_length must be an integer")
        
        if 'max_token_budget' in memory and not isinstance(memory['max_token_budget'], int):
            self.errors.append("Memory max_token_budget must be an integer")
    
    def _validate_logging_section(self):
        """Validate logging section"""
        if 'logging' not in self.config:
            return
        
        logging_config = self.config['logging']
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if 'level' in logging_config and logging_config['level'] not in valid_levels:
            self.errors.append(f"Logging level must be one of: {', '.join(valid_levels)}")
        
        if 'max_size_mb' in logging_config and not isinstance(logging_config['max_size_mb'], (int, float)):
            self.errors.append("Logging max_size_mb must be a number")
    
    def _validate_security_section(self):
        """Validate security section"""
        if 'security' not in self.config:
            return
        
        security = self.config['security']
        
        if 'allow_read_file_content' in security and not isinstance(security['allow_read_file_content'], bool):
            self.errors.append("Security allow_read_file_content must be a boolean")
        
        if 'allow_network_access' in security and not isinstance(security['allow_network_access'], bool):
            self.errors.append("Security allow_network_access must be a boolean")
    
    def _validate_ui_section(self):
        """Validate UI section"""
        if 'ui' not in self.config:
            return
        
        ui = self.config['ui']
        
        if 'port' in ui and not isinstance(ui['port'], int):
            self.errors.append("UI port must be an integer")
        
        if 'port' in ui and (ui['port'] < 1 or ui['port'] > 65535):
            self.errors.append("UI port must be between 1 and 65535")
    
    def _validate_paths(self):
        """Validate file paths in configuration"""
        if 'security' in self.config and 'sensitivity_patterns_path' in self.config['security']:
            path = self.config['security']['sensitivity_patterns_path']
            if not os.path.exists(path):
                self.warnings.append(f"Sensitivity patterns file does not exist: {path}")
    
    def create_default_config(self, output_path: Optional[str] = None) -> bool:
        """Create a default configuration file"""
        try:
            output_path = output_path or self.config_path
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
            
            logger.info(f"Default configuration created at: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating default configuration: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get the validated configuration"""
        return self.config.copy()
    
    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings.copy() 