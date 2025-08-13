"""
Hendrix Pipeline - Main Pipeline Class
Coordinates all components for video analysis
"""

import os
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline coordinator for Hendrix video analysis"""
    
    def __init__(self, config=None):
        """Initialize pipeline with configuration"""
        self.config = config or {}
        self.components = []
        
    def process_video(self, video_path, output_dir=None, components=None, verbose=False):
        """
        Process a video through the pipeline
        
        Args:
            video_path: Path to input video
            output_dir: Output directory (auto-generated if None)
            components: List of components to run
            verbose: Enable verbose output
            
        Returns:
            dict: Results including output directory
        """
        # Setup logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
            
        # Validate input
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
            
        # Setup output directory
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_name = video_path.stem
            output_dir = Path(f"outputs/{video_name}_{timestamp}")
        else:
            output_dir = Path(output_dir)
            
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Components to run
        if components is None:
            components = ["video", "audio", "caption"]
            
        results = {
            "video_path": str(video_path),
            "output_dir": str(output_dir),
            "components_run": components,
            "status": "success"
        }
        
        # Run components (simplified for testing)
        try:
            if "video" in components:
                logger.info("Running video analysis...")
                video_results = self._run_video_analysis(video_path, output_dir)
                results["video_analysis"] = video_results
                
            if "audio" in components:
                logger.info("Running audio analysis...")
                audio_results = self._run_audio_analysis(video_path, output_dir)
                results["audio_analysis"] = audio_results
                
            if "caption" in components:
                logger.info("Generating captions...")
                caption_results = self._run_caption_generation(output_dir)
                results["captions"] = caption_results
                
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            
        # Save results
        results_file = output_dir / "pipeline_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
        
    def _run_video_analysis(self, video_path, output_dir):
        """Run video analysis component (mock implementation)"""
        # Create mock results for testing
        results = {
            "scenes": [
                {"start": 0.0, "end": 5.0, "shots": 3},
                {"start": 5.0, "end": 10.0, "shots": 2}
            ],
            "total_scenes": 2,
            "total_shots": 5
        }
        
        # Save to file
        scenes_file = output_dir / "video_analysis" / "scenes.json"
        scenes_file.parent.mkdir(exist_ok=True)
        with open(scenes_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results
        
    def _run_audio_analysis(self, video_path, output_dir):
        """Run audio analysis component (mock implementation)"""
        # Create mock results
        results = {
            "transcripts": [
                {"start": 0.0, "end": 3.0, "text": "Hello world", "speaker": "SPEAKER_1"},
                {"start": 3.0, "end": 6.0, "text": "This is a test", "speaker": "SPEAKER_1"}
            ],
            "speakers": ["SPEAKER_1"]
        }
        
        # Save to file
        audio_file = output_dir / "character_dialogue" / "character_data.json"
        audio_file.parent.mkdir(exist_ok=True)
        with open(audio_file, 'w') as f:
            json.dump({"characters": {}, "transcripts": results["transcripts"]}, f, indent=2)
            
        return results
        
    def _run_caption_generation(self, output_dir):
        """Generate captions (mock implementation)"""
        # Create mock captions
        captions = [
            {
                "start_time": 0.0,
                "end_time": 5.0,
                "caption": "A peaceful scene begins with someone saying hello",
                "speaker": "SPEAKER_1"
            },
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "caption": "The test continues with more dialogue",
                "speaker": "SPEAKER_1"
            }
        ]
        
        # Save multiple formats
        caption_dir = output_dir / "comprehensive_captions"
        caption_dir.mkdir(exist_ok=True)
        
        # JSON format
        with open(caption_dir / "captions.json", 'w') as f:
            json.dump({"captions": captions}, f, indent=2)
            
        # SRT format
        with open(caption_dir / "captions.srt", 'w') as f:
            for i, cap in enumerate(captions, 1):
                f.write(f"{i}\n")
                f.write(f"{self._format_time(cap['start_time'])} --> {self._format_time(cap['end_time'])}\n")
                f.write(f"{cap['caption']}\n\n")
                
        # Simple HTML timeline
        with open(caption_dir / "timeline.html", 'w') as f:
            f.write("<html><body><h1>Video Timeline</h1>\n")
            for cap in captions:
                f.write(f"<p><b>{cap['start_time']:.1f}s - {cap['end_time']:.1f}s:</b> {cap['caption']}</p>\n")
            f.write("</body></html>")
            
        return {"total_captions": len(captions)}
        
    def _format_time(self, seconds):
        """Format time for SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')