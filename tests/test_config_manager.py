"""
Unit tests for ConfigManager
"""
import pytest
from pathlib import Path
import tempfile
import yaml

from hendrix.core.config import ConfigManager


class TestConfigManager:
    """Test configuration management functionality"""
    
    def test_default_config_loading(self):
        """Test loading default configuration"""
        config = ConfigManager()
        assert config is not None
        assert config.config is not None
        assert "components" in config.config
    
    def test_custom_config_loading(self, temp_dir):
        """Test loading custom configuration file"""
        # Create test config
        test_config = {
            "test_key": "test_value",
            "components": {
                "video_analysis": {
                    "enabled": True
                }
            }
        }
        
        config_path = temp_dir / "test_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Load config
        config = ConfigManager(str(config_path))
        assert config.get("test_key") == "test_value"
        assert config.get("components.video_analysis.enabled") is True
    
    def test_dot_notation_access(self):
        """Test accessing config values with dot notation"""
        config = ConfigManager()
        config.config = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        assert config.get("level1.level2.level3") == "value"
        assert config.get("level1.level2") == {"level3": "value"}
        assert config.get("nonexistent.key", "default") == "default"
    
    def test_config_setting(self):
        """Test setting configuration values"""
        config = ConfigManager()
        config.config = {}
        
        # Set nested value
        config.set("new.nested.value", 42)
        assert config.get("new.nested.value") == 42
        
        # Overwrite existing value
        config.set("new.nested.value", 100)
        assert config.get("new.nested.value") == 100
    
    def test_environment_variable_expansion(self):
        """Test environment variable expansion in config"""
        import os
        
        # Set test environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        config = ConfigManager()
        config.config = {
            "path": "${TEST_VAR}/subfolder",
            "direct": "$TEST_VAR"
        }
        
        # Expand variables
        config._expand_env_vars()
        
        assert config.get("path") == "test_value/subfolder"
        assert config.get("direct") == "test_value"
        
        # Cleanup
        del os.environ["TEST_VAR"]
    
    def test_profile_loading(self):
        """Test loading different profiles"""
        profiles = ["fast", "balanced", "quality", "test"]
        
        for profile in profiles:
            config = ConfigManager(profile=profile)
            # Each profile should load without errors
            assert config is not None
            assert config.config is not None
    
    def test_model_listing(self):
        """Test listing available models"""
        from components.config_manager import list_all_models
        
        models = list_all_models()
        assert isinstance(models, dict)
        
        # Should have categories
        assert any(key in models for key in ["vision_language", "whisper", "diarization"])
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = ConfigManager()
        
        # Required keys should exist
        assert config.get("components") is not None
        assert config.get("pipeline") is not None
        
        # Component configs should be dictionaries
        components = config.get("components", {})
        for component_name, component_config in components.items():
            assert isinstance(component_config, dict)
    
    def test_config_merge(self):
        """Test merging configurations"""
        config = ConfigManager()
        
        base_config = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        
        override_config = {
            "b": {
                "c": 20,
                "e": 4
            },
            "f": 5
        }
        
        merged = config._merge_configs(base_config, override_config)
        
        assert merged["a"] == 1
        assert merged["b"]["c"] == 20  # Overridden
        assert merged["b"]["d"] == 3   # Preserved
        assert merged["b"]["e"] == 4   # Added
        assert merged["f"] == 5        # Added
    
    def test_component_config_extraction(self):
        """Test extracting component-specific configuration"""
        config = ConfigManager()
        config.config = {
            "components": {
                "video_analysis": {
                    "setting1": "value1"
                },
                "captioning": {
                    "setting2": "value2"
                }
            }
        }
        
        video_config = config.get_component_config("video_analysis")
        assert video_config["setting1"] == "value1"
        
        caption_config = config.get_component_config("captioning")
        assert caption_config["setting2"] == "value2"
        
        # Non-existent component
        missing_config = config.get_component_config("nonexistent")
        assert missing_config == {}
    
    def test_config_persistence(self, temp_dir):
        """Test saving and loading configuration"""
        config = ConfigManager()
        config.set("test.value", 123)
        config.set("test.nested.value", "abc")
        
        # Save config
        save_path = temp_dir / "saved_config.yaml"
        config.save(str(save_path))
        
        # Load saved config
        loaded_config = ConfigManager(str(save_path))
        assert loaded_config.get("test.value") == 123
        assert loaded_config.get("test.nested.value") == "abc"
    
    def test_config_cli_overrides(self):
        """Test CLI argument overrides"""
        config = ConfigManager()
        config.config = {
            "components": {
                "video_analysis": {
                    "enabled": True
                }
            }
        }
        
        # Simulate CLI overrides
        overrides = {
            "components.video_analysis.enabled": False,
            "new.setting": "value"
        }
        
        for key, value in overrides.items():
            config.set(key, value)
        
        assert config.get("components.video_analysis.enabled") is False
        assert config.get("new.setting") == "value"
    
    def test_active_model_management(self):
        """Test active model selection and swapping"""
        config = ConfigManager()
        
        # Mock model configuration
        config.config = {
            "components": {
                "captioning": {
                    "vision_language_model": {
                        "active_model": "llava_7b"
                    }
                }
            }
        }
        
        # Get active model
        active_model = config.get("components.captioning.vision_language_model.active_model")
        assert active_model == "llava_7b"
        
        # Set new active model
        config.set_active_model("llava_13b")
        new_model = config.get("components.captioning.vision_language_model.active_model")
        assert new_model == "llava_13b"