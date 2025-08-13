"""
Output Format Handlers for Comprehensive Captions

This module provides formatters for various caption output formats including
JSON, SRT, WebVTT, and more.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import html

logger = logging.getLogger(__name__)


class OutputFormatter:
    """
    Base class for handling multiple output formats
    """
    
    def __init__(self, formats: List[str], include_metadata: bool = True):
        """
        Initialize the output formatter
        
        Args:
            formats: List of output formats to generate
            include_metadata: Whether to include metadata in outputs
        """
        self.formats = formats
        self.include_metadata = include_metadata
        
        # Map format names to handler methods
        self.format_handlers = {
            "json": self.save_json,
            "srt": self.save_srt,
            "webvtt": self.save_webvtt,
            "txt": self.save_text,
            "html": self.save_html
        }
    
    def save_all_formats(self, data: Dict[str, Any], output_dir: Path, 
                        base_filename: str = "captions") -> Dict[str, str]:
        """
        Save captions in all configured formats
        
        Args:
            data: Caption data with metadata and captions list
            output_dir: Directory to save files
            base_filename: Base filename without extension
            
        Returns:
            Dictionary mapping format to saved file path
        """
        saved_files = {}
        
        for format_name in self.formats:
            if format_name in self.format_handlers:
                try:
                    filepath = self.format_handlers[format_name](
                        data, output_dir, base_filename
                    )
                    saved_files[format_name] = str(filepath)
                    logger.info(f"Saved {format_name} format to {filepath}")
                except Exception as e:
                    logger.error(f"Failed to save {format_name} format: {e}")
            else:
                logger.warning(f"Unknown format: {format_name}")
        
        return saved_files
    
    def save_json(self, data: Dict[str, Any], output_dir: Path, 
                  base_filename: str) -> Path:
        """Save captions in JSON format"""
        filepath = output_dir / f"{base_filename}.json"
        
        # Clean data for JSON serialization
        output_data = {
            "captions": data["captions"]
        }
        
        if self.include_metadata:
            output_data["metadata"] = data.get("metadata", {})
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_srt(self, data: Dict[str, Any], output_dir: Path, 
                 base_filename: str) -> Path:
        """Save captions in SRT (SubRip) format"""
        filepath = output_dir / f"{base_filename}.srt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(data["captions"], 1):
                # Write subtitle number
                f.write(f"{i}\n")
                
                # Write timecode
                start_time = self._seconds_to_srt_time(caption["start_time"])
                end_time = self._seconds_to_srt_time(caption["end_time"])
                f.write(f"{start_time} --> {end_time}\n")
                
                # Write caption text
                caption_text = caption["caption"]
                
                # Add speaker information if dialogue is present
                if caption.get("has_dialogue") and caption.get("characters"):
                    # Prepend character names for context
                    characters = ", ".join(caption["characters"][:2])  # Limit to 2 names
                    caption_text = f"[{characters}] {caption_text}"
                
                f.write(f"{caption_text}\n\n")
        
        return filepath
    
    def save_webvtt(self, data: Dict[str, Any], output_dir: Path, 
                    base_filename: str) -> Path:
        """Save captions in WebVTT format"""
        filepath = output_dir / f"{base_filename}.vtt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write WebVTT header
            f.write("WEBVTT\n")
            f.write("Kind: captions\n")
            
            if self.include_metadata and "metadata" in data:
                f.write(f"Language: en\n")
                generated_at = data["metadata"].get("generated_at", "")
                if generated_at:
                    f.write(f"Generated: {generated_at}\n")
            
            f.write("\n")
            
            # Write cues
            for i, caption in enumerate(data["captions"], 1):
                # Write cue identifier (optional but helpful)
                f.write(f"SCENE_{caption['scene_id']:03d}\n")
                
                # Write timecode
                start_time = self._seconds_to_webvtt_time(caption["start_time"])
                end_time = self._seconds_to_webvtt_time(caption["end_time"])
                f.write(f"{start_time} --> {end_time}")
                
                # Add position/alignment if characters are speaking
                if caption.get("has_dialogue"):
                    f.write(" align:left line:90%")
                
                f.write("\n")
                
                # Write caption with optional styling
                caption_text = caption["caption"]
                
                # Add styling for dialogue
                if caption.get("has_dialogue") and caption.get("characters"):
                    characters = ", ".join(caption["characters"][:2])
                    caption_text = f"<v {characters}>{caption_text}</v>"
                
                f.write(f"{caption_text}\n\n")
        
        return filepath
    
    def save_text(self, data: Dict[str, Any], output_dir: Path, 
                  base_filename: str) -> Path:
        """Save captions in plain text format"""
        filepath = output_dir / f"{base_filename}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header if metadata is included
            if self.include_metadata and "metadata" in data:
                f.write("=" * 80 + "\n")
                f.write("COMPREHENSIVE VIDEO CAPTIONS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {data['metadata'].get('generated_at', 'Unknown')}\n")
                f.write(f"Total Scenes: {data['metadata'].get('total_scenes', 0)}\n")
                total_duration = data['metadata'].get('total_duration', 0)
                f.write(f"Total Duration: {self._format_duration(total_duration)}\n")
                f.write("=" * 80 + "\n\n")
            
            # Write captions
            for caption in data["captions"]:
                # Scene header
                f.write(f"[Scene {caption['scene_id']}] ")
                f.write(f"{self._format_timestamp(caption['start_time'])} - ")
                f.write(f"{self._format_timestamp(caption['end_time'])}\n")
                
                # Characters if present
                if caption.get("characters"):
                    f.write(f"Characters: {', '.join(caption['characters'])}\n")
                
                # Caption text
                f.write(f"{caption['caption']}\n")
                f.write("-" * 40 + "\n\n")
        
        return filepath
    
    def save_html(self, data: Dict[str, Any], output_dir: Path, 
                  base_filename: str) -> Path:
        """Save captions in HTML format with styling"""
        filepath = output_dir / f"{base_filename}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Captions - {base_filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .caption {{
            background-color: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .caption-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .scene-number {{
            font-weight: bold;
            color: #3498db;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .characters {{
            background-color: #e8f4f8;
            padding: 5px 10px;
            border-radius: 3px;
            margin-bottom: 10px;
            font-size: 0.9em;
        }}
        .caption-text {{
            line-height: 1.8;
        }}
        .has-dialogue {{
            border-left: 4px solid #3498db;
            padding-left: 16px;
        }}
    </style>
</head>
<body>
    <h1>Comprehensive Video Captions</h1>
"""
        
        # Add metadata section
        if self.include_metadata and "metadata" in data:
            meta = data["metadata"]
            html_content += f"""
    <div class="metadata">
        <strong>Generated:</strong> {meta.get('generated_at', 'Unknown')}<br>
        <strong>Total Scenes:</strong> {meta.get('total_scenes', 0)}<br>
        <strong>Total Duration:</strong> {self._format_duration(meta.get('total_duration', 0))}
    </div>
"""
        
        # Add captions
        for caption in data["captions"]:
            dialogue_class = "has-dialogue" if caption.get("has_dialogue") else ""
            
            html_content += f"""
    <div class="caption {dialogue_class}">
        <div class="caption-header">
            <span class="scene-number">Scene {caption['scene_id']}</span>
            <span class="timestamp">
                {self._format_timestamp(caption['start_time'])} - 
                {self._format_timestamp(caption['end_time'])}
            </span>
        </div>
"""
            
            if caption.get("characters"):
                characters_html = html.escape(", ".join(caption["characters"]))
                html_content += f"""
        <div class="characters">
            <strong>Characters:</strong> {characters_html}
        </div>
"""
            
            caption_text = html.escape(caption["caption"])
            html_content += f"""
        <div class="caption-text">
            {caption_text}
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    # Helper methods
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _seconds_to_webvtt_time(self, seconds: float) -> str:
        """Convert seconds to WebVTT time format (HH:MM:SS.mmm)"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS"""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)


if __name__ == "__main__":
    # Test the output formatter
    sample_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_scenes": 2,
            "total_duration": 30.5
        },
        "captions": [
            {
                "caption_id": "SCENE_CAP_001",
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 15.0,
                "duration": 15.0,
                "caption": "The scene opens with two characters discussing their plans for the day.",
                "characters": ["John", "Sarah"],
                "has_dialogue": True
            },
            {
                "caption_id": "SCENE_CAP_002",
                "scene_id": 2,
                "start_time": 15.0,
                "end_time": 30.5,
                "duration": 15.5,
                "caption": "The camera pans across a beautiful landscape as the sun sets.",
                "characters": [],
                "has_dialogue": False
            }
        ]
    }
    
    # Create formatter and test
    formatter = OutputFormatter(["json", "srt", "webvtt", "txt", "html"])
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    saved_files = formatter.save_all_formats(sample_data, output_dir, "test_captions")
    
    print("Saved files:")
    for format_name, filepath in saved_files.items():
        print(f"  {format_name}: {filepath}")