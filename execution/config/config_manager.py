#!/usr/bin/env python3
"""
ConfigManager - Enterprise-grade configuration management system.

Provides centralized, scalable configuration management with:
- Environment-specific configurations
- Dynamic configuration updates
- Validation and schema enforcement
- Hot reloading capabilities
- Secure credential management
"""

import json
import logging
import os
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionConfig:
    """Configuration for agent execution."""
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    health_check_interval: int = 30
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    safety_level: str = "high"


@dataclass 
class SuggestionConfig:
    """Configuration for suggestion engine."""
    confidence_threshold: float = 0.7
    backend_ws_url: str = "ws://localhost:8765"
    enable_proactive_mode: bool = True
    suggestion_cache_size: int = 100
    auto_retry_failed_suggestions: bool = True
    max_suggestions_per_minute: int = 10


@dataclass
class AutomationConfig:
    """Configuration for automation system."""
    safety_level: str = "high"
    mouse_speed: str = "medium"
    click_delay: float = 0.1
    typing_speed: str = "medium"
    confirmation_timeout: float = 30.0
    enable_sound: bool = True
    screenshot_quality: int = 95
    max_automation_sequence_length: int = 50


@dataclass
class MemoryConfig:
    """Configuration for memory system."""
    memory_path: str = "logs/agent_memory.db"
    cache_size: int = 1000
    cleanup_interval_days: int = 30
    enable_learning: bool = True
    context_retention_hours: int = 24
    max_task_history: int = 10000


@dataclass
class IntegrationConfig:
    """Configuration for workflow integration."""
    legacy_support_enabled: bool = True
    legacy_ws_url: str = "ws://127.0.0.1:8765"
    bridge_message_timeout: float = 10.0
    enable_message_logging: bool = True
    max_legacy_connections: int = 5


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_encryption: bool = True
    api_key_rotation_days: int = 30
    max_failed_auth_attempts: int = 5
    session_timeout_minutes: int = 60
    enable_audit_logging: bool = True
    allowed_ip_ranges: List[str] = field(default_factory=list)


@dataclass
class ExecutionConfig:
    """Master configuration for the execution system."""
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Core components
    agent: AgentExecutionConfig = field(default_factory=AgentExecutionConfig)
    suggestion: SuggestionConfig = field(default_factory=SuggestionConfig)
    automation: AutomationConfig = field(default_factory=AutomationConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigFileHandler(FileSystemEventHandler):
    """Handles configuration file changes for hot reloading."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml', '.json')):
            logger.info(f"Configuration file changed: {event.src_path}")
            self.config_manager._reload_config()


class ConfigManager:
    """
    Enterprise-grade configuration management system.
    
    Features:
    - Multi-format support (YAML, JSON, environment variables)
    - Environment-specific configurations
    - Hot reloading with file watching
    - Configuration validation
    - Secure credential management
    - Dynamic updates
    - Thread-safe operations
    """
    
    def __init__(self, config_path: Optional[str] = None, enable_hot_reload: bool = True):
        """Initialize configuration manager."""
        self.config_path = config_path or self._find_config_file()
        self.enable_hot_reload = enable_hot_reload
        
        # Configuration storage
        self.config: ExecutionConfig = ExecutionConfig()
        self.config_lock = threading.RLock()
        
        # Hot reload setup
        self.observer: Optional[Observer] = None
        self.file_handler: Optional[ConfigFileHandler] = None
        
        # Load initial configuration
        self._load_config()
        
        # Setup hot reloading
        if enable_hot_reload:
            self._setup_hot_reload()
        
        logger.info(f"ConfigManager initialized with config: {self.config_path}")
    
    def _find_config_file(self) -> str:
        """Find configuration file in standard locations."""
        potential_paths = [
            "config/execution_config.yaml",
            "config/execution_config.yml", 
            "config/execution_config.json",
            "execution_config.yaml",
            "execution_config.yml",
            "execution_config.json"
        ]
        
        for path in potential_paths:
            if Path(path).exists():
                return path
        
        # Create default config if none found
        default_path = "config/execution_config.yaml"
        self._create_default_config(default_path)
        return default_path
    
    def _create_default_config(self, path: str) -> None:
        """Create default configuration file."""
        config_dir = Path(path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        default_config = ExecutionConfig()
        
        with open(path, 'w') as f:
            yaml.dump(asdict(default_config), f, default_flow_style=False, indent=2)
        
        logger.info(f"Created default configuration: {path}")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if not Path(self.config_path).exists():
                logger.warning(f"Configuration file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.json'):
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)
            
            # Merge with environment variables
            config_data = self._merge_environment_variables(config_data)
            
            # Validate and create config object
            self.config = self._create_config_from_dict(config_data)
            
            # Apply environment-specific overrides
            self._apply_environment_overrides()
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _merge_environment_variables(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables into configuration."""
        # Environment variable mapping
        env_mappings = {
            'EXECUTION_ENVIRONMENT': 'environment',
            'EXECUTION_DEBUG': 'debug',
            'EXECUTION_LOG_LEVEL': 'agent.log_level',
            'EXECUTION_SAFETY_LEVEL': 'automation.safety_level',
            'SUGGESTION_CONFIDENCE_THRESHOLD': 'suggestion.confidence_threshold',
            'SUGGESTION_BACKEND_URL': 'suggestion.backend_ws_url',
            'MEMORY_PATH': 'memory.memory_path',
            'MEMORY_CACHE_SIZE': 'memory.cache_size',
            'SECURITY_ENABLE_ENCRYPTION': 'security.enable_encryption'
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_data, config_path, self._convert_env_value(env_value))
        
        return config_data
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> ExecutionConfig:
        """Create ExecutionConfig object from dictionary."""
        try:
            # Create nested config objects
            agent_config = AgentExecutionConfig(**config_data.get('agent', {}))
            suggestion_config = SuggestionConfig(**config_data.get('suggestion', {}))
            automation_config = AutomationConfig(**config_data.get('automation', {}))
            memory_config = MemoryConfig(**config_data.get('memory', {}))
            integration_config = IntegrationConfig(**config_data.get('integration', {}))
            security_config = SecurityConfig(**config_data.get('security', {}))
            
            # Create main config
            return ExecutionConfig(
                environment=config_data.get('environment', 'development'),
                debug=config_data.get('debug', False),
                agent=agent_config,
                suggestion=suggestion_config,
                automation=automation_config,
                memory=memory_config,
                integration=integration_config,
                security=security_config,
                custom=config_data.get('custom', {})
            )
            
        except Exception as e:
            logger.error(f"Failed to create config object: {e}")
            raise
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides."""
        if self.config.environment == 'production':
            # Production overrides
            self.config.debug = False
            self.config.agent.log_level = 'WARNING'
            self.config.security.enable_encryption = True
            self.config.security.enable_audit_logging = True
        
        elif self.config.environment == 'development':
            # Development overrides
            self.config.debug = True
            self.config.agent.log_level = 'DEBUG'
            self.config.suggestion.enable_proactive_mode = True
        
        elif self.config.environment == 'staging':
            # Staging overrides
            self.config.debug = False
            self.config.agent.log_level = 'INFO'
            self.config.security.enable_audit_logging = True
    
    def _setup_hot_reload(self) -> None:
        """Setup hot reloading for configuration files."""
        try:
            config_dir = Path(self.config_path).parent
            
            self.file_handler = ConfigFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(self.file_handler, str(config_dir), recursive=False)
            self.observer.start()
            
            logger.info("Hot reload enabled for configuration")
            
        except Exception as e:
            logger.warning(f"Failed to setup hot reload: {e}")
    
    def _reload_config(self) -> None:
        """Reload configuration from file."""
        with self.config_lock:
            try:
                old_config = self.config
                self._load_config()
                
                # Notify about configuration changes
                self._notify_config_change(old_config, self.config)
                
                logger.info("Configuration reloaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
    
    def _notify_config_change(self, old_config: ExecutionConfig, new_config: ExecutionConfig) -> None:
        """Notify about configuration changes."""
        # This would trigger callbacks to notify components about config changes
        # For now, just log the changes
        if old_config.agent.log_level != new_config.agent.log_level:
            logger.info(f"Log level changed: {old_config.agent.log_level} -> {new_config.agent.log_level}")
        
        if old_config.automation.safety_level != new_config.automation.safety_level:
            logger.info(f"Safety level changed: {old_config.automation.safety_level} -> {new_config.automation.safety_level}")
    
    # ========== Public API ==========
    
    def get_config(self) -> ExecutionConfig:
        """Get current configuration."""
        with self.config_lock:
            return self.config
    
    def get_agent_config(self) -> AgentExecutionConfig:
        """Get agent configuration."""
        with self.config_lock:
            return self.config.agent
    
    def get_suggestion_config(self) -> SuggestionConfig:
        """Get suggestion configuration."""
        with self.config_lock:
            return self.config.suggestion
    
    def get_automation_config(self) -> AutomationConfig:
        """Get automation configuration."""
        with self.config_lock:
            return self.config.automation
    
    def get_memory_config(self) -> MemoryConfig:
        """Get memory configuration."""
        with self.config_lock:
            return self.config.memory
    
    def get_integration_config(self) -> IntegrationConfig:
        """Get integration configuration."""
        with self.config_lock:
            return self.config.integration
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration."""
        with self.config_lock:
            return self.config.security
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration dynamically."""
        with self.config_lock:
            old_config = self.config
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    self.config.custom[key] = value
            
            # Notify about changes
            self._notify_config_change(old_config, self.config)
            
            logger.info(f"Configuration updated: {list(updates.keys())}")
    
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        save_path = path or self.config_path
        
        with self.config_lock:
            try:
                config_dict = asdict(self.config)
                
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(save_path, 'w') as f:
                    if save_path.endswith('.json'):
                        json.dump(config_dict, f, indent=2)
                    else:
                        yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                
                logger.info(f"Configuration saved to: {save_path}")
                
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                raise
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return any errors."""
        errors = []
        
        with self.config_lock:
            # Validate agent config
            if self.config.agent.max_concurrent_tasks <= 0:
                errors.append("agent.max_concurrent_tasks must be positive")
            
            if self.config.agent.task_timeout_seconds <= 0:
                errors.append("agent.task_timeout_seconds must be positive")
            
            # Validate suggestion config
            if not 0.0 <= self.config.suggestion.confidence_threshold <= 1.0:
                errors.append("suggestion.confidence_threshold must be between 0.0 and 1.0")
            
            # Validate automation config
            if self.config.automation.safety_level not in ['low', 'medium', 'high', 'maximum']:
                errors.append("automation.safety_level must be one of: low, medium, high, maximum")
            
            # Validate memory config
            if self.config.memory.cache_size <= 0:
                errors.append("memory.cache_size must be positive")
            
            # Validate security config
            if self.config.security.session_timeout_minutes <= 0:
                errors.append("security.session_timeout_minutes must be positive")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring."""
        with self.config_lock:
            return {
                'environment': self.config.environment,
                'debug': self.config.debug,
                'config_file': self.config_path,
                'hot_reload_enabled': self.enable_hot_reload,
                'agent': {
                    'max_concurrent_tasks': self.config.agent.max_concurrent_tasks,
                    'log_level': self.config.agent.log_level,
                    'safety_level': self.config.agent.safety_level
                },
                'suggestion': {
                    'confidence_threshold': self.config.suggestion.confidence_threshold,
                    'proactive_mode': self.config.suggestion.enable_proactive_mode
                },
                'automation': {
                    'safety_level': self.config.automation.safety_level,
                    'mouse_speed': self.config.automation.mouse_speed
                },
                'memory': {
                    'cache_size': self.config.memory.cache_size,
                    'learning_enabled': self.config.memory.enable_learning
                },
                'security': {
                    'encryption_enabled': self.config.security.enable_encryption,
                    'audit_logging': self.config.security.enable_audit_logging
                }
            }
    
    # ========== Cleanup ==========
    
    def cleanup(self) -> None:
        """Cleanup configuration manager resources."""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            logger.info("ConfigManager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()