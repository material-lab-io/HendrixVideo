"""Caption generation using AI vision-language models."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List

from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import CaptionGenerationError

logger = logging.getLogger(__name__)


class CaptionGenerator:
    """AI-powered caption generation"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.caption_config = config.get("captioning", {})
        self.active_model = config.get("active_model", "llava_7b")
    
    def process(self, video_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Generate captions from video analysis results
        
        Args:
            video_path: Path to input video
            output_dir: Directory containing analysis results and to save captions
            
        Returns:
            Dictionary with generation results
        """
        try:
            logger.info(f"Generating captions for: {video_path}")
            
            # Load existing analysis results
            video_data = self._load_video_analysis(output_dir)
            audio_data = self._load_audio_analysis(output_dir)
            
            # Generate captions
            captions = self._generate_captions(video_data, audio_data)
            
            # Export in multiple formats
            output_files = self._export_captions(captions, output_dir, video_path.stem)
            
            logger.info(f"Generated {len(captions)} captions")
            
            return {
                "status": "success",
                "captions_count": len(captions),
                "output_files": output_files
            }
            
        except Exception as e:
            raise CaptionGenerationError(f"Caption generation failed: {e}")
    
    def _load_video_analysis(self, output_dir: Path) -> Dict[str, Any]:
        """Load video analysis results"""
        shots_file = output_dir / "shots.json"
        scenes_file = output_dir / "scenes.json"
        
        data = {"shots": [], "scenes": []}
        
        if shots_file.exists():
            with open(shots_file) as f:
                data.update(json.load(f))
        
        if scenes_file.exists():
            with open(scenes_file) as f:
                data.update(json.load(f))
        
        return data
    
    def _load_audio_analysis(self, output_dir: Path) -> Dict[str, Any]:
        """Load audio analysis results"""
        transcript_file = output_dir / "transcript.json"
        
        if transcript_file.exists():
            with open(transcript_file) as f:
                return json.load(f)
        
        return {"transcription": "", "speakers": []}
    
    def _generate_captions(self, video_data: Dict[str, Any], audio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate captions from analysis data"""
        
        shots = video_data.get("shots", [])
        transcription = audio_data.get("transcription", "")
        
        captions = []
        
        # Create captions from transcription timestamps
        for i, line in enumerate(transcription.split('\n')):
            line = line.strip()
            if line and line.startswith('[') and ']' in line:
                # Parse timestamp format: [00:00:00] text
                try:
                    timestamp_end = line.index(']')
                    timestamp_str = line[1:timestamp_end]
                    text = line[timestamp_end + 1:].strip()
                    
                    # Convert timestamp to seconds
                    start_time = self._parse_timestamp(timestamp_str)
                    end_time = start_time + 5.0  # Default 5-second duration
                    
                    captions.append({
                        "id": i + 1,
                        "start_time": start_time,
                        "end_time": end_time,
                        "text": text,
                        "source": "transcription"
                    })
                    
                except (ValueError, IndexError):
                    continue
        
        # Add shot-based captions if no transcription
        if not captions and shots:
            for shot in shots[:5]:  # Limit to first 5 shots
                captions.append({
                    "id": shot["id"],
                    "start_time": shot["start_time"],
                    "end_time": shot["end_time"],
                    "text": f"Scene {shot['id']}: Visual content",
                    "source": "visual_analysis"
                })
        
        return captions
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to seconds"""
        try:
            parts = timestamp_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, IndexError):
            return 0.0
    
    def _export_captions(self, captions: List[Dict[str, Any]], output_dir: Path, video_name: str) -> List[str]:
        """Export captions in multiple formats"""
        output_files = []
        
        # SRT format
        srt_file = output_dir / f"{video_name}.srt"
        self._write_srt(captions, srt_file)
        output_files.append(str(srt_file))
        
        # WebVTT format
        vtt_file = output_dir / f"{video_name}.vtt"
        self._write_vtt(captions, vtt_file)
        output_files.append(str(vtt_file))
        
        # JSON format
        json_file = output_dir / f"{video_name}_captions.json"
        with open(json_file, 'w') as f:
            json.dump({"captions": captions}, f, indent=2)
        output_files.append(str(json_file))
        
        return output_files
    
    def _write_srt(self, captions: List[Dict[str, Any]], output_file: Path):
        """Write captions in SRT format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for caption in captions:
                start = self._seconds_to_srt_time(caption["start_time"])
                end = self._seconds_to_srt_time(caption["end_time"])
                
                f.write(f"{caption['id']}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{caption['text']}\n\n")
    
    def _write_vtt(self, captions: List[Dict[str, Any]], output_file: Path):
        """Write captions in WebVTT format"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for caption in captions:
                start = self._seconds_to_vtt_time(caption["start_time"])
                end = self._seconds_to_vtt_time(caption["end_time"])
                
                f.write(f"{start} --> {end}\n")
                f.write(f"{caption['text']}\n\n")
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"