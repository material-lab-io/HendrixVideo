"""
Hendrix Pipeline Configuration Manager
Handles configuration loading, model swapping, and profile management
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from copy import deepcopy
import logging

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
        self.config_dir = Path(config_path).parent
        self.base_config = self._load_yaml(config_path)
        self.active_config = deepcopy(self.base_config)
        
        # Load additional configs
        self.models_registry = self._load_yaml(self.config_dir / "models.yaml")
        
        # Apply profile if specified
        if profile:
            self.apply_profile(profile)
            
        # Apply any manual overrides
        if overrides:
            self._apply_overrides(overrides)
            
        # Expand environment variables
        self._expand_env_vars()
        
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        path = Path(path)
        if not path.exists():
            logger.warning(f"Configuration file not found: {path}")
            return {}
            
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
            
    def _save_yaml(self, config: Dict[str, Any], path: str):
        """Save configuration to YAML file"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
    def _apply_overrides(self, overrides: Dict[str, Any]):
        """Apply configuration overrides using dot notation"""
        for key, value in overrides.items():
            self._set_nested(self.active_config, key, value)
            
    def _set_nested(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
            
        current[keys[-1]] = value
        
    def _get_nested(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
                
        return current
        
    def _expand_env_vars(self):
        """Expand environment variables in configuration"""
        def expand_value(value):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                return os.environ.get(env_var, value)
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(v) for v in value]
            return value
            
        self.active_config = expand_value(self.active_config)
        
    def apply_profile(self, profile_name: str):
        """Apply a predefined profile"""
        profiles = self.base_config.get('profiles', {})
        
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found. Available: {list(profiles.keys())}")
            
        profile = profiles[profile_name]
        logger.info(f"Applying profile: {profile.get('name', profile_name)}")
        
        # Apply profile overrides
        overrides = profile.get('overrides', {})
        self._apply_overrides(overrides)
        
    def set_active_model(self, model_name: str):
        """Change the active model"""
        available_models = self.base_config.get('models', {})
        
        if model_name not in available_models:
            raise ValueError(f"Model '{model_name}' not found. Available: {list(available_models.keys())}")
            
        self.active_config['active_model'] = model_name
        logger.info(f"Active model set to: {model_name}")
        
    def get_model_config(self, model_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific model
        
        Args:
            model_type: Type of model (vision_language, whisper, etc.)
                       If None, returns active VLM model config
        """
        if model_type is None:
            # Return active vision-language model
            active_model = self.active_config.get('active_model')
            return self.active_config.get('models', {}).get(active_model, {})
        else:
            # Return specific model type config
            return self.active_config.get(f'{model_type}_models', {})
            
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """Get configuration for a specific component"""
        return self.active_config.get('components', {}).get(component, {})
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        return self._get_nested(self.active_config, key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        self._set_nested(self.active_config, key, value)
        
    def list_available_models(self, model_type: Optional[str] = None) -> List[str]:
        """List available models"""
        if model_type:
            models = self.models_registry.get(f'{model_type}_models', {})
            return list(models.keys())
        else:
            # List all VLM models
            return list(self.base_config.get('models', {}).keys())
            
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model from registry"""
        # Search in all model categories
        for category in ['vision_language_models', 'audio_models', 'video_models']:
            category_models = self.models_registry.get(category, {})
            for provider, models in category_models.items():
                if model_name in models:
                    return models[model_name]
                    
        return {}
        
    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of issues"""
        issues = []
        
        # Check active model exists
        active_model = self.active_config.get('active_model')
        if active_model not in self.active_config.get('models', {}):
            issues.append(f"Active model '{active_model}' not found in models configuration")
            
        # Check required directories
        output_dir = self.get('output.base_directory')
        if not output_dir:
            issues.append("Output directory not specified")
            
        # Check device configuration
        device = self.get('pipeline.device')
        if device.startswith('cuda') and not self._check_cuda_available():
            issues.append(f"CUDA device '{device}' specified but CUDA not available")
            
        return issues
        
    def _check_cuda_available(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
            
    def save_config(self, path: str):
        """Save current configuration to file"""
        self._save_yaml(self.active_config, path)
        logger.info(f"Configuration saved to: {path}")
        
    def load_config(self, path: str):
        """Load configuration from file"""
        new_config = self._load_yaml(path)
        if new_config:
            self.active_config = new_config
            logger.info(f"Configuration loaded from: {path}")
            
    def export_runtime_config(self) -> Dict[str, Any]:
        """Export configuration suitable for runtime use"""
        # Remove unnecessary sections for runtime
        runtime_config = deepcopy(self.active_config)
        runtime_config.pop('profiles', None)
        runtime_config.pop('development', None)
        
        # Add runtime information
        runtime_config['runtime'] = {
            'config_manager_version': '2.0.0',
            'active_profile': self.get('profile', 'custom'),
            'timestamp': str(Path.ctime(Path.cwd()))
        }
        
        return runtime_config


# Convenience functions for quick model swapping
def quick_swap_model(model_name: str, config_path: str = "configs/base_config.yaml"):
    """Quickly swap to a different model"""
    config = ConfigManager(config_path)
    config.set_active_model(model_name)
    return config
    

def list_all_models(config_path: str = "configs/base_config.yaml"):
    """List all available models"""
    config = ConfigManager(config_path)
    
    print("Available Vision-Language Models:")
    for model in config.list_available_models():
        info = config.get_model_info(model)
        print(f"  - {model}: {info.get('name', 'No description')}")
        
    print("\nAvailable Audio Models:")
    for model in config.list_available_models('whisper'):
        print(f"  - {model}")
        
    print("\nAvailable Profiles:")
    profiles = config.base_config.get('profiles', {})
    for profile_name, profile_data in profiles.items():
        print(f"  - {profile_name}: {profile_data.get('description', 'No description')}")


if __name__ == "__main__":
    # Example usage
    config = ConfigManager("configs/base_config.yaml", profile="balanced")
    
    # List available models
    print("Available models:", config.list_available_models())
    
    # Switch model
    config.set_active_model("llava_13b")
    
    # Get model configuration
    model_config = config.get_model_config()
    print("Active model config:", model_config)
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print("Configuration issues:", issues)