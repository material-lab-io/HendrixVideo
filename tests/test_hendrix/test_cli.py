"""Tests for hendrix CLI module."""

import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch

from hendrix.cli import main, analyze, verify, config, list_models
from hendrix.core.config import ConfigManager


class TestCLI:
    """Test CLI functionality."""
    
    def test_main_help(self):
        """Test main CLI help."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Hendrix Video Analysis Pipeline" in result.output
    
    def test_analyze_help(self):
        """Test analyze command help."""
        runner = CliRunner()
        result = runner.invoke(analyze, ['--help'])
        assert result.exit_code == 0
        assert "Analyze a video file" in result.output
    
    def test_verify_command(self):
        """Test verify command."""
        runner = CliRunner()
        result = runner.invoke(verify)
        # Should complete without error
        assert result.exit_code == 0
        assert "Installation verification" in result.output
    
    def test_config_command(self):
        """Test config command."""
        runner = CliRunner()
        result = runner.invoke(config)
        assert result.exit_code == 0
        assert "Configuration" in result.output
    
    def test_list_models_command(self):
        """Test list-models command."""
        runner = CliRunner()
        result = runner.invoke(list_models)
        assert result.exit_code == 0
        assert "Available Models" in result.output
    
    @patch('hendrix.core.pipeline.Pipeline')
    def test_analyze_with_valid_video(self, mock_pipeline):
        """Test analyze command with valid video."""
        # Setup mock
        mock_pipeline.return_value.analyze.return_value = {
            "video": {"status": "success"},
            "audio": {"status": "success"}, 
            "caption": {"status": "success"}
        }
        
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            
            result = runner.invoke(analyze, [str(video_path)])
            assert result.exit_code == 0
            assert "Analysis complete" in result.output
    
    def test_analyze_with_nonexistent_video(self):
        """Test analyze command with nonexistent video."""
        runner = CliRunner()
        result = runner.invoke(analyze, ['nonexistent_video.mp4'])
        assert result.exit_code != 0
        assert "does not exist" in result.output
    
    def test_analyze_with_profile(self):
        """Test analyze command with profile option."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            
            with patch('hendrix.core.pipeline.Pipeline') as mock_pipeline:
                mock_pipeline.return_value.analyze.return_value = {
                    "video": {"status": "success"},
                    "audio": {"status": "success"},
                    "caption": {"status": "success"}
                }
                
                result = runner.invoke(analyze, [str(video_path), '--profile', 'fast'])
                assert result.exit_code == 0
    
    def test_analyze_with_components(self):
        """Test analyze command with components option."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4" 
            video_path.touch()
            
            with patch('hendrix.core.pipeline.Pipeline') as mock_pipeline:
                mock_pipeline.return_value.analyze.return_value = {
                    "video": {"status": "success"},
                    "audio": {"status": "success"}
                }
                
                result = runner.invoke(analyze, [
                    str(video_path), 
                    '--components', 'video', 'audio'
                ])
                assert result.exit_code == 0
    
    def test_analyze_with_output_dir(self):
        """Test analyze command with output directory option."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            
            with patch('hendrix.core.pipeline.Pipeline') as mock_pipeline:
                mock_pipeline.return_value.analyze.return_value = {
                    "video": {"status": "success"},
                    "audio": {"status": "success"},
                    "caption": {"status": "success"}
                }
                
                result = runner.invoke(analyze, [
                    str(video_path),
                    '--output', str(output_dir)
                ])
                assert result.exit_code == 0