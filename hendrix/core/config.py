"""
Hendrix Pipeline Configuration Manager
Handles configuration loading, model swapping, and profile management
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from copy import deepcopy
import logging

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Unified configuration management for Hendrix pipeline"""
    
    def __init__(
        self, 
        config_path: str = "configs/base_config.yaml",
        profile: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to base configuration file
            profile: Profile name to apply (fast, quality, test, etc.)
            overrides: Dictionary of configuration overrides
        """
        # Find the config directory relative to project root
        project_root = self._find_project_root()
        
        self.config_dir = project_root / "configs"
        self.config_file = self.config_dir / "base_config.yaml"
        
        # Load base configuration
        try:
            self.base_config = self._load_yaml(self.config_file)
            self.active_config = deepcopy(self.base_config)
        except Exception as e:
            logger.warning(f"Could not load config from {self.config_file}: {e}")
            self.base_config = self._get_default_config()
            self.active_config = deepcopy(self.base_config)
        
        # Load additional configs if they exist
        try:
            models_file = self.config_dir / "models.yaml"
            if models_file.exists():
                self.models_registry = self._load_yaml(models_file)
            else:
                self.models_registry = self._get_default_models_registry()
        except Exception as e:
            logger.warning(f"Could not load models registry: {e}")
            self.models_registry = self._get_default_models_registry()
        
        # Apply profile if specified
        if profile:
            self.apply_profile(profile)
            
        # Apply any manual overrides
        if overrides:
            self._apply_overrides(overrides)
            
        # Expand environment variables
        self._expand_env_vars()

    @property
    def config(self) -> Dict[str, Any]:
        """Backward compatibility property for accessing active config"""
        return self.active_config

    def _find_project_root(self) -> Path:
        """Find the project root directory"""
        current = Path.cwd()
        
        # Look for project indicators
        for parent in [current] + list(current.parents):
            if any(
                (parent / marker).exists() 
                for marker in ["pyproject.toml", "setup.py", "hendrix_pipeline.py", "configs"]
            ):
                return parent
        
        # Fallback to current directory
        return current

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config files are not available"""
        return {
            "models": {
                "llava_7b": {
                    "provider": "llava",
                    "model": "llava-hf/llava-1.5-7b-hf",
                    "device_config": {
                        "device_map": "auto",
                        "torch_dtype": "float16",
                        "load_in_8bit": False,
                        "load_in_4bit": False,
                        "low_cpu_mem_usage": True
                    }
                }
            },
            "active_model": "llava_7b",
            "audio_models": {
                "whisper": {"model": "base"}
            },
            "pipeline": {
                "device": None,
                "batch_size": 32
            },
            "output": {
                "formats": ["json", "srt", "vtt", "html"]
            }
        }

    def _get_default_models_registry(self) -> Dict[str, Any]:
        """Get default models registry"""
        return {
            "vision_language": {
                "llava_7b": {"size": "7B", "memory_gb": 14},
                "llava_13b": {"size": "13B", "memory_gb": 24}
            },
            "audio": {
                "whisper_base": {"size": "Base", "memory_gb": 1},
                "whisper_large": {"size": "Large", "memory_gb": 3}
            }
        }
        
    def _load_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'models.llava_7b.device_config.device_map')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.active_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        config = self.active_config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def apply_profile(self, profile_name: str) -> None:
        """Apply a configuration profile"""
        profile_file = self.config_dir / "profiles" / f"{profile_name}.yaml"
        
        if not profile_file.exists():
            # Use built-in profiles
            profile_config = self._get_builtin_profile(profile_name)
        else:
            profile_config = self._load_yaml(profile_file)
        
        if profile_config:
            self.active_config = self._merge_configs(self.active_config, profile_config)
            logger.info(f"Applied profile: {profile_name}")
    
    def _get_builtin_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get built-in profile configuration"""
        profiles = {
            "fast": {
                "active_model": "llava_7b",
                "pipeline": {"batch_size": 16},
                "models": {
                    "llava_7b": {
                        "device_config": {"load_in_8bit": True}
                    }
                }
            },
            "quality": {
                "active_model": "llava_13b",
                "pipeline": {"batch_size": 8},
                "models": {
                    "llava_13b": {
                        "device_config": {"load_in_8bit": False, "torch_dtype": "float16"}
                    }
                }
            },
            "test": {
                "active_model": "mock",
                "pipeline": {"batch_size": 4},
                "models": {
                    "mock": {
                        "provider": "mock",
                        "model": "mock-model",
                        "device_config": {"device": "cpu"}
                    }
                }
            },
            "balanced": {
                "active_model": "llava_7b",
                "pipeline": {"batch_size": 32},
            }
        }
        return profiles.get(profile_name)
    
    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply configuration overrides"""
        self.active_config = self._merge_configs(self.active_config, overrides)
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries and return the result"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _expand_env_vars(self) -> None:
        """Expand environment variables in configuration values"""
        self.active_config = self._expand_dict_env_vars(self.active_config)
    
    def _expand_dict_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in dictionary values"""
        if isinstance(obj, dict):
            return {key: self._expand_dict_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_dict_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return os.path.expandvars(obj)
        else:
            return obj
    
    def set_active_model(self, model_name: str) -> None:
        """Set the active vision-language model"""
        if model_name in self.get("models", {}):
            self.set("active_model", model_name)
            logger.info(f"Active model set to: {model_name}")
        else:
            available = list(self.get("models", {}).keys())
            raise ConfigurationError(
                f"Model '{model_name}' not found. Available models: {available}"
            )
    
    def get_active_model_config(self) -> Dict[str, Any]:
        """Get configuration for the currently active model"""
        active_model = self.get("active_model")
        if not active_model:
            raise ConfigurationError("No active model configured")
        
        model_config = self.get(f"models.{active_model}")
        if not model_config:
            raise ConfigurationError(f"Configuration not found for model: {active_model}")
        
        return model_config
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models"""
        return self.get("models", {})
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return any issues"""
        issues = []
        
        # Check if active model exists
        active_model = self.get("active_model")
        if active_model and active_model not in self.get("models", {}):
            issues.append(f"Active model '{active_model}' not found in models registry")
        
        # Check required sections exist
        required_sections = ["models", "pipeline", "output"]
        for section in required_sections:
            if not self.get(section):
                issues.append(f"Missing required configuration section: {section}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Export current configuration as dictionary"""
        return deepcopy(self.active_config)
    
    def save(self, path: Union[str, Path]) -> None:
        """Save current configuration to file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.active_config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config to {path}: {e}")


def list_all_models(config_path: str = "configs/base_config.yaml") -> None:
    """Utility function to list all available models"""
    try:
        config = ConfigManager(config_path)
        
        print("Available Vision-Language Models:")
        vlm_models = config.get("models", {})
        for name, info in vlm_models.items():
            desc = info.get("description", "No description")
            print(f"  - {name}: {desc}")
        
        print("\nAvailable Audio Models:")
        audio_models = config.get("audio_models", {})
        for category, models in audio_models.items():
            print(f"  {category}:")
            if isinstance(models, dict):
                for name, info in models.items():
                    print(f"    - {name}: {info}")
        
        print("\nAvailable Profiles:")
        profiles = ["fast", "balanced", "quality", "test"]
        for profile in profiles:
            profile_config = config._get_builtin_profile(profile)
            if profile_config:
                desc = {
                    "fast": "Optimized for speed with reduced quality",
                    "balanced": "Good balance between speed and quality", 
                    "quality": "Maximum quality with all features enabled",
                    "test": "For development and testing with minimal resources"
                }.get(profile, "")
                print(f"  - {profile}: {desc}")
        
    except Exception as e:
        print(f"Error listing models: {e}")