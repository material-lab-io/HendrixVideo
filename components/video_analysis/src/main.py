#!/usr/bin/env python3
"""
Video Analysis Pipeline - Main Orchestrator

This pipeline implements a three-stage video analysis process:
1. Shot Detection (AutoShot)
2. Scene Construction (LLaVA)
3. Cinematic Analysis (Specialized VLM)
"""

import argparse
import json
import logging
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import from components
current_dir = Path(__file__).parent
components_dir = current_dir.parent.parent
sys.path.insert(0, str(components_dir))

from video_analysis.src.schemas.analysis import AnalysisResult, VideoMetadata
from video_analysis.src.pipeline.shot_detection import ShotDetectionPipeline
from video_analysis.src.pipeline.scene_construction import SceneConstructionPipeline
from video_analysis.src.pipeline.cinematic_analysis import CinematicAnalysisPipeline
from video_analysis.src.utils.video_utils import VideoProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoAnalysisPipeline:
    """Main orchestrator for the three-stage video analysis pipeline."""
    
    def __init__(self, config_path: str = "config.yaml", output_dir: str = None):
        # If config path is relative, look for it relative to this file
        if not Path(config_path).is_absolute() and not Path(config_path).exists():
            # Try to find config relative to the script location
            script_dir = Path(__file__).parent.parent
            possible_config = script_dir / config_path
            if possible_config.exists():
                config_path = str(possible_config)
        
        self.config = self._load_config(config_path)
        
        # Override output directory if specified
        if output_dir:
            self._override_output_dir(output_dir)
        
        self._setup_directories()
        
        # Initialize pipeline stages AFTER config is updated
        self.shot_detector = ShotDetectionPipeline(self.config)
        self.scene_constructor = SceneConstructionPipeline(self.config)
        self.cinematic_analyzer = CinematicAnalysisPipeline(self.config)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _override_output_dir(self, output_dir: str):
        """Override output directory in configuration."""
        output_path = Path(output_dir).resolve()  # Use absolute path
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure output section exists
        if 'output' not in self.config:
            self.config['output'] = {}
        
        # Update config output paths to use absolute paths
        for key in ['shots_file', 'scenes_file', 'analysis_file', 'combined_output']:
            if key in self.config['output']:
                filename = Path(self.config['output'][key]).name
            else:
                # Default filenames if not in config
                defaults = {
                    'shots_file': 'shots.json',
                    'scenes_file': 'scenes.json',
                    'analysis_file': 'analysis.json',
                    'combined_output': 'video_analysis_complete.json'
                }
                filename = defaults.get(key, f'{key}.json')
            
            new_path = str(output_path / filename)
            self.config['output'][key] = new_path
            logger.info(f"Set {key} to: {new_path}")
        
        # Also update the keyframes directory
        if 'pipeline' not in self.config:
            self.config['pipeline'] = {}
        self.config['pipeline']['keyframes_directory'] = str(output_path / 'keyframes')
    
    def _setup_directories(self):
        """Create necessary directories."""
        dirs = [
            self.config.get('general', {}).get('temp_directory', './temp'),
            self.config.get('pipeline', {}).get('keyframes_directory', './keyframes')
        ]
        
        # Also ensure output directory exists
        output_files = [
            self.config.get('output', {}).get('shots_file', './output/shots.json'),
            self.config.get('output', {}).get('scenes_file', './output/scenes.json'),
            self.config.get('output', {}).get('analysis_file', './output/analysis.json'),
            self.config.get('output', {}).get('combined_output', './output/video_analysis_complete.json')
        ]
        
        for output_file in output_files:
            output_dir = Path(output_file).parent
            if output_dir not in dirs:
                dirs.append(str(output_dir))
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def analyze_video(self, video_path: str, resume_from: str = None) -> AnalysisResult:
        """
        Run the complete video analysis pipeline.
        
        Args:
            video_path: Path to the input video file
            resume_from: Resume from a specific stage ('shots', 'scenes', or None)
            
        Returns:
            Complete AnalysisResult object
        """
        logger.info(f"Starting video analysis pipeline for: {video_path}")
        start_time = time.time()
        
        # Get video metadata
        video_metadata = self._get_video_metadata(video_path)
        
        # Stage 1: Shot Detection
        if resume_from is None:
            logger.info("=" * 50)
            logger.info("STAGE 1: Shot Detection")
            logger.info("=" * 50)
            shots = self.shot_detector.process_video(
                video_path, 
                save_intermediate=self.config.get('general', {}).get('save_intermediate_results', True)
            )
        else:
            logger.info(f"Resuming from saved {resume_from} data")
            shots = self.shot_detector.load_shots(
                self.config.get('output', {}).get('shots_file', 'shots.json')
            )
        
        # Stage 2: Scene Construction
        if resume_from not in ['scenes']:
            logger.info("=" * 50)
            logger.info("STAGE 2: Scene Construction")
            logger.info("=" * 50)
            scenes = self.scene_constructor.process_shots(
                shots,
                save_intermediate=self.config.get('general', {}).get('save_intermediate_results', True)
            )
        else:
            scenes = self.scene_constructor.load_scenes(
                self.config.get('output', {}).get('scenes_file', 'scenes.json')
            )
        
        # Stage 3: Cinematic Analysis
        logger.info("=" * 50)
        logger.info("STAGE 3: Cinematic Analysis")
        logger.info("=" * 50)
        cinematic_analysis = self.cinematic_analyzer.analyze_video(shots, scenes)
        
        # Create final analysis result
        total_time = time.time() - start_time
        analysis_result = AnalysisResult(
            video_metadata=video_metadata,
            shots=shots,
            scenes=scenes,
            processing_time=total_time,
            cinematic_analysis=cinematic_analysis
        )
        
        # Save complete analysis
        self._save_complete_analysis(analysis_result)
        
        logger.info("=" * 50)
        logger.info(f"Video analysis completed in {total_time:.2f} seconds")
        logger.info(f"Total shots: {len(shots)}")
        logger.info(f"Total scenes: {len(scenes)}")
        logger.info("=" * 50)
        
        return analysis_result
    
    def _get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Extract video metadata."""
        with VideoProcessor(video_path) as vp:
            metadata_dict = vp.get_video_metadata()
            return VideoMetadata(**metadata_dict)
    
    def _save_complete_analysis(self, analysis_result: AnalysisResult):
        """Save the complete analysis result."""
        output_file = Path(self.config.get('output', {}).get('combined_output', 'video_analysis_complete.json'))
        
        try:
            # Ensure parent directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(analysis_result.to_dict(), f, indent=2)
            logger.info(f"Saved complete analysis to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save complete analysis: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Video Analysis Pipeline - Three-stage analysis using AutoShot, LLaVA, and Cinematic VLM"
    )
    
    parser.add_argument(
        "video_path",
        help="Path to the input video file"
    )
    
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--resume-from",
        choices=["shots", "scenes"],
        help="Resume from a previous stage using saved intermediate results"
    )
    
    parser.add_argument(
        "--output-dir",
        help="Override output directory for results"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Verify video file exists
    if not Path(args.video_path).exists():
        logger.error(f"Video file not found: {args.video_path}")
        sys.exit(1)
    
    try:
        # Initialize pipeline with output directory
        pipeline = VideoAnalysisPipeline(args.config, output_dir=args.output_dir)
        
        # Run analysis
        result = pipeline.analyze_video(args.video_path, args.resume_from)
        
        # Print summary
        print("\nAnalysis Complete!")
        print(f"Video: {result.video_metadata.filename}")
        print(f"Duration: {result.video_metadata.duration:.2f} seconds")
        print(f"Total Shots: {len(result.shots)}")
        print(f"Total Scenes: {len(result.scenes)}")
        print(f"Processing Time: {result.processing_time:.2f} seconds")
        
        # Print scene summaries
        print("\nScene Summaries:")
        for scene in result.scenes[:5]:  # Show first 5 scenes
            print(f"  Scene {scene.scene_id}: {scene.summary}")
        
        if len(result.scenes) > 5:
            print(f"  ... and {len(result.scenes) - 5} more scenes")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()