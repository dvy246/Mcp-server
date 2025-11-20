"""
Configuration Loader
====================

Loads configuration from config.yaml and environment variables.
Environment variables take precedence over config file values.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
import re

logger = logging.getLogger(__name__)


def expand_env_vars(value: Any) -> Any:
    """
    Recursively expand environment variables in configuration values.
    Supports ${VAR_NAME:-default_value} syntax.
    
    Args:
        value: Configuration value (can be str, dict, list, etc.)
        
    Returns:
        Value with environment variables expanded
    """
    if isinstance(value, str):
        # Pattern: ${VAR_NAME:-default_value} or ${VAR_NAME}
        pattern = r'\$\{([^}:]+)(?::-(.*?))?\}'
        
        def replace_env(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ''
            return os.getenv(var_name, default_value)
        
        return re.sub(pattern, replace_env, value)
    
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    
    return value


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and expand environment variables.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary with expanded environment variables
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables
        config = expand_env_vars(config)
        
        logger.info(f"Configuration loaded from {config_path}")
        return config
    
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise


def get_enabled_servers(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get only enabled servers from configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Dictionary of enabled servers
    """
    servers = config.get('servers', {})
    enabled_servers = {
        name: server_config 
        for name, server_config in servers.items() 
        if server_config.get('enabled', True)
    }
    
    # Remove 'enabled' key from server configs
    for server_config in enabled_servers.values():
        server_config.pop('enabled', None)
    
    return enabled_servers


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration has required fields.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    # Check for API key
    api_key_env = config.get('llm', {}).get('api_key_env', 'GEMINI_API_KEY')
    if not os.getenv(api_key_env):
        raise ValueError(f"Environment variable {api_key_env} not set")
    
    # Check servers exist
    if not config.get('servers'):
        raise ValueError("No servers configured")
    
    logger.info("Configuration validation passed")
    return True
