"""
Configuration handling for Endpoint Finder.
"""

import os
import yaml


def load_config(config_path):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path (str): Path to the configuration file.
        
    Returns:
        dict: Configuration dictionary.
        
    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the configuration file is not valid YAML.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing configuration file: {e}")


def get_default_config():
    """
    Get the default configuration.
    
    Returns:
        dict: Default configuration dictionary.
    """
    return {
        "github": {
            "token": None,
        },
        "scan": {
            "languages": ["python", "javascript", "java", "php", "ruby", "go"],
            "exclude_dirs": [".git", "node_modules", "venv", ".venv", "__pycache__"],
        },
        "output": {
            "format": "text",
            "file": None,
        },
    }


def merge_configs(default_config, user_config):
    """
    Merge the default configuration with the user configuration.
    
    Args:
        default_config (dict): Default configuration dictionary.
        user_config (dict): User configuration dictionary.
        
    Returns:
        dict: Merged configuration dictionary.
    """
    merged_config = default_config.copy()
    
    for section, values in user_config.items():
        if section in merged_config and isinstance(merged_config[section], dict):
            merged_config[section].update(values)
        else:
            merged_config[section] = values
    
    return merged_config