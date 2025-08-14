"""
Hendrix Pipeline - Main pipeline coordinator
Orchestrates video analysis, audio processing, and caption generation
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from .config import ConfigManager
from .exceptions import HendrixError, VideoProcessingError

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline coordinator for Hendrix video analysis"""
    
    def __init__(self, config: Optional[Union[str, ConfigManager]] = None, profile: str = "balanced"):
        """
        Initialize pipeline with configuration
        
        Args:
            config: Configuration manager or path to config file
            profile: Configuration profile to use
        """
        if isinstance(config, str):
            self.config = ConfigManager(config, profile=profile)
        elif isinstance(config, ConfigManager):
            self.config = config
        else:
            self.config = ConfigManager(profile=profile)
            
        self.project_root = self._find_project_root()
        
        # Set up logging
        self._setup_logging()
        
        logger.info(f"Initialized Hendrix Pipeline with profile: {profile}")
        
    def _find_project_root(self) -> Path:
        """Find the project root directory"""
        current = Path(__file__).parent
        
        # Go up from hendrix/core to project root
        for parent in [current] + list(current.parents):
            if any(
                (parent / marker).exists() 
                for marker in ["pyproject.toml", "setup.py", "hendrix_pipeline.py"]
            ):
                return parent
        
        # Fallback to current working directory
        return Path.cwd()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        log_level = self.config.get("logging.level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def analyze(
        self, 
        video_path: str,
        output_dir: Optional[str] = None,
        components: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze a video through the complete pipeline
        
        Args:
            video_path: Path to input video file
            output_dir: Output directory (auto-generated if not provided)
            components: List of components to run ["video", "audio", "caption"]
            **kwargs: Additional options
            
        Returns:
            Dictionary containing results and metadata
        """
        try:
            # Validate input
            video_path = Path(video_path)
            if not video_path.exists():
                raise VideoProcessingError(f"Video file not found: {video_path}")
            
            # Set up output directory
            if output_dir is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = self.project_root / "outputs" / f"{video_path.stem}_{timestamp}"
            else:
                output_dir = Path(output_dir)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Processing video: {video_path}")
            logger.info(f"Output directory: {output_dir}")
            
            # Determine which components to run
            if components is None:
                components = ["video", "audio", "caption"]
            
            # Process each component
            results = {
                "input_video": str(video_path),
                "output_dir": str(output_dir),
                "components_run": components,
                "timestamp": datetime.now().isoformat(),
                "config": self.config.to_dict(),
                "results": {}
            }
            
            for component in components:
                logger.info(f"Running {component} analysis component...")
                
                try:
                    component_result = self._run_component(
                        component, video_path, output_dir, **kwargs
                    )
                    results["results"][component] = component_result
                    logger.info(f"✓ {component} analysis completed")
                    
                except Exception as e:
                    logger.error(f"✗ {component} analysis failed: {e}")
                    results["results"][component] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    
                    # Continue with other components unless it's a critical failure
                    if component == "video":  # Video analysis is foundational
                        logger.warning("Video analysis failed - continuing with available data")
            
            # Save consolidated results
            results_file = output_dir / "pipeline_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Pipeline completed. Results saved to: {results_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise HendrixError(f"Pipeline execution failed: {e}")
    
    def _run_component(
        self, 
        component: str, 
        video_path: Path, 
        output_dir: Path, 
        **kwargs
    ) -> Dict[str, Any]:
        """Run a specific pipeline component"""
        
        if component == "video":
            return self._run_video_analysis(video_path, output_dir, **kwargs)
        elif component == "audio":
            return self._run_audio_processing(video_path, output_dir, **kwargs)
        elif component == "caption":
            return self._run_caption_generation(video_path, output_dir, **kwargs)
        else:
            raise ValueError(f"Unknown component: {component}")
    
    def _run_video_analysis(self, video_path: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Run video analysis component"""
        try:
            # Try to import and use the video analysis component
            from hendrix.video.analyzer import VideoAnalyzer
            
            analyzer = VideoAnalyzer(self.config)
            results = analyzer.process(video_path, output_dir)
            
            return {
                "status": "success",
                "output_files": results.get("output_files", []),
                "shots_detected": results.get("shots_count", 0),
                "scenes_created": results.get("scenes_count", 0)
            }
            
        except ImportError:
            # Fallback to subprocess call
            logger.warning("Video analyzer not available, using subprocess fallback")
            return self._run_video_analysis_subprocess(video_path, output_dir, **kwargs)
    
    def _run_video_analysis_subprocess(self, video_path: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Run video analysis using subprocess (fallback)"""
        try:
            # Look for video analysis script
            script_paths = [
                self.project_root / "components" / "video_analysis" / "src" / "main.py",
                self.project_root / "hendrix" / "video" / "main.py"
            ]
            
            script_path = None
            for path in script_paths:
                if path.exists():
                    script_path = path
                    break
            
            if not script_path:
                return {
                    "status": "skipped",
                    "reason": "Video analysis script not found"
                }
            
            # Run the script
            cmd = [
                sys.executable, str(script_path),
                str(video_path),
                "--output-dir", str(output_dir),
                "--config", str(self.config.config_file)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "stdout": result.stdout,
                    "method": "subprocess"
                }
            else:
                return {
                    "status": "failed",
                    "error": result.stderr or result.stdout,
                    "returncode": result.returncode
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "method": "subprocess"
            }
    
    def _run_audio_processing(self, video_path: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Run audio processing component"""
        try:
            # Try to import audio processor
            from hendrix.audio.processor import AudioProcessor
            
            processor = AudioProcessor(self.config)
            results = processor.process(video_path, output_dir)
            
            return {
                "status": "success",
                "transcription_file": results.get("transcription_file"),
                "speakers_detected": results.get("speakers_count", 0)
            }
            
        except ImportError:
            logger.warning("Audio processor not available")
            return {
                "status": "skipped",
                "reason": "Audio processing not available in current installation"
            }
        except Exception as e:
            return {
                "status": "failed", 
                "error": str(e)
            }
    
    def _run_caption_generation(self, video_path: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Run caption generation component"""
        try:
            # Try to import caption generator
            from hendrix.captioning.generator import CaptionGenerator
            
            generator = CaptionGenerator(self.config)
            results = generator.process(video_path, output_dir)
            
            return {
                "status": "success",
                "caption_files": results.get("output_files", [])
            }
            
        except ImportError:
            logger.warning("Caption generator not available")
            return {
                "status": "skipped", 
                "reason": "Caption generation not available in current installation"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def verify_installation(self) -> Dict[str, Any]:
        """Verify that the pipeline installation is working correctly"""
        verification = {
            "status": "success",
            "issues": [],
            "components": {}
        }
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if sys.version_info < (3, 8):
            verification["issues"].append(f"Python {python_version} detected. Python 3.8+ required.")
            verification["status"] = "failed"
        
        # Check required packages
        required_packages = [
            ("torch", "torch"),
            ("torchvision", "torchvision"),
            ("numpy", "numpy"),
            ("opencv-python", "cv2"),
            ("pandas", "pandas"),
            ("pyyaml", "yaml"),
            ("tqdm", "tqdm")
        ]
        
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                verification["components"][package_name] = "✓"
            except ImportError:
                verification["issues"].append(f"Missing package: {package_name}")
                verification["components"][package_name] = "✗"
                verification["status"] = "failed"
        
        # Check CUDA availability
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                verification["components"]["CUDA"] = f"✓ ({device_name})"
            else:
                verification["components"]["CUDA"] = "⚠ Not available (CPU mode will be used)"
        except:
            verification["components"]["CUDA"] = "✗ Error checking CUDA"
        
        # Check FFmpeg
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            verification["components"]["FFmpeg"] = "✓"
        except:
            verification["issues"].append("FFmpeg not found. Please install FFmpeg.")
            verification["components"]["FFmpeg"] = "✗"
            verification["status"] = "failed"
        
        # Check configuration
        config_issues = self.config.validate_config()
        if config_issues:
            verification["issues"].extend(config_issues)
            verification["status"] = "failed"
        else:
            verification["components"]["Configuration"] = "✓"
        
        return verification
    
    # Convenience methods for backward compatibility
    def process_video(self, *args, **kwargs):
        """Alias for analyze method"""
        return self.analyze(*args, **kwargs)