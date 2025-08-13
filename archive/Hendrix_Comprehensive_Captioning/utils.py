"""
Utility Functions for Comprehensive Captioning

This module provides helper functions for the captioning pipeline.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import re
import hashlib

logger = logging.getLogger(__name__)


def find_latest_session(base_path: Union[str, Path], pattern: str = "session_*") -> Optional[Path]:
    """
    Find the latest session directory matching a pattern
    
    Args:
        base_path: Base directory to search
        pattern: Glob pattern for session directories
        
    Returns:
        Path to latest session or None
    """
    base_path = Path(base_path)
    sessions = sorted(base_path.glob(pattern))
    
    if not sessions:
        return None
        
    # Sort by timestamp in directory name
    def extract_timestamp(path):
        # Extract timestamp from session_YYYYMMDD_HHMMSS format
        match = re.search(r'session_(\d{8}_\d{6})', path.name)
        if match:
            return match.group(1)
        return path.name
    
    sessions.sort(key=lambda p: extract_timestamp(p), reverse=True)
    return sessions[0]


def align_time_segments(segment1: Dict[str, float], segment2: Dict[str, float], 
                       tolerance: float = 0.5) -> float:
    """
    Calculate time alignment score between two segments
    
    Args:
        segment1: First segment with start_time and end_time
        segment2: Second segment with start_time and end_time
        tolerance: Time tolerance in seconds
        
    Returns:
        Alignment score (0.0 to 1.0)
    """
    start1, end1 = segment1.get('start_time', 0), segment1.get('end_time', 0)
    start2, end2 = segment2.get('start_time', 0), segment2.get('end_time', 0)
    
    # Calculate overlap
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    overlap_duration = max(0, overlap_end - overlap_start)
    
    # Calculate union
    union_start = min(start1, start2)
    union_end = max(end1, end2)
    union_duration = union_end - union_start
    
    if union_duration == 0:
        return 0.0
        
    # IoU (Intersection over Union) score
    iou = overlap_duration / union_duration
    
    # Apply tolerance bonus
    if abs(start1 - start2) <= tolerance and abs(end1 - end2) <= tolerance:
        iou = min(1.0, iou * 1.2)
    
    return iou


def merge_overlapping_segments(segments: List[Dict[str, Any]], 
                             time_key_start: str = "start_time",
                             time_key_end: str = "end_time",
                             tolerance: float = 0.1) -> List[Dict[str, Any]]:
    """
    Merge overlapping or adjacent time segments
    
    Args:
        segments: List of segments with time information
        time_key_start: Key for start time
        time_key_end: Key for end time
        tolerance: Tolerance for considering segments adjacent
        
    Returns:
        List of merged segments
    """
    if not segments:
        return []
    
    # Sort by start time
    sorted_segments = sorted(segments, key=lambda s: s.get(time_key_start, 0))
    
    merged = []
    current = sorted_segments[0].copy()
    
    for segment in sorted_segments[1:]:
        current_end = current.get(time_key_end, 0)
        segment_start = segment.get(time_key_start, 0)
        
        # Check if segments overlap or are adjacent
        if segment_start <= current_end + tolerance:
            # Merge segments
            current[time_key_end] = max(current_end, segment.get(time_key_end, 0))
            
            # Merge other fields (customize as needed)
            if 'text' in current and 'text' in segment:
                current['text'] = current['text'] + " " + segment['text']
            
        else:
            # No overlap, add current and start new
            merged.append(current)
            current = segment.copy()
    
    # Add the last segment
    merged.append(current)
    
    return merged


def format_time_range(start_seconds: float, end_seconds: float, 
                     format_type: str = "readable") -> str:
    """
    Format a time range for display
    
    Args:
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        format_type: "readable", "srt", "webvtt", or "compact"
        
    Returns:
        Formatted time range string
    """
    if format_type == "readable":
        start_str = format_seconds_readable(start_seconds)
        end_str = format_seconds_readable(end_seconds)
        duration = format_seconds_readable(end_seconds - start_seconds)
        return f"{start_str} - {end_str} ({duration})"
    
    elif format_type == "srt":
        start_str = format_seconds_srt(start_seconds)
        end_str = format_seconds_srt(end_seconds)
        return f"{start_str} --> {end_str}"
    
    elif format_type == "webvtt":
        start_str = format_seconds_webvtt(start_seconds)
        end_str = format_seconds_webvtt(end_seconds)
        return f"{start_str} --> {end_str}"
    
    else:  # compact
        start_str = format_seconds_compact(start_seconds)
        end_str = format_seconds_compact(end_seconds)
        return f"[{start_str}-{end_str}]"


def format_seconds_readable(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS"""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_seconds_srt(seconds: float) -> str:
    """Format seconds as SRT timestamp (HH:MM:SS,mmm)"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_seconds_webvtt(seconds: float) -> str:
    """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_seconds_compact(seconds: float) -> str:
    """Format seconds in compact form"""
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    secs = total_seconds % 60
    
    if minutes > 0:
        return f"{minutes}m{secs}s"
    else:
        return f"{secs}s"


def sanitize_text_for_captions(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text for use in captions
    
    Args:
        text: Input text
        max_length: Maximum length (truncate if longer)
        
    Returns:
        Sanitized text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove or replace problematic characters
    text = text.replace('\n', ' ')
    text = text.replace('\r', '')
    text = text.replace('\t', ' ')
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text.strip()


def estimate_reading_time(text: str, wpm: int = 180) -> float:
    """
    Estimate reading time for text in seconds
    
    Args:
        text: Text to estimate
        wpm: Words per minute reading speed
        
    Returns:
        Estimated time in seconds
    """
    words = len(text.split())
    minutes = words / wpm
    return minutes * 60


def generate_caption_id(scene_id: int, timestamp: float) -> str:
    """
    Generate a unique caption ID
    
    Args:
        scene_id: Scene identifier
        timestamp: Timestamp in seconds
        
    Returns:
        Unique caption ID
    """
    # Create a hash of timestamp for uniqueness
    time_hash = hashlib.md5(str(timestamp).encode()).hexdigest()[:6]
    return f"CAP_{scene_id:03d}_{time_hash}"


def validate_time_sequence(segments: List[Dict[str, Any]], 
                         start_key: str = "start_time",
                         end_key: str = "end_time") -> List[str]:
    """
    Validate that time segments are in proper sequence
    
    Args:
        segments: List of segments with time information
        start_key: Key for start time
        end_key: Key for end time
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not segments:
        return errors
    
    # Check each segment
    for i, segment in enumerate(segments):
        start = segment.get(start_key)
        end = segment.get(end_key)
        
        # Check segment has required fields
        if start is None:
            errors.append(f"Segment {i} missing {start_key}")
            continue
        if end is None:
            errors.append(f"Segment {i} missing {end_key}")
            continue
        
        # Check start < end
        if start >= end:
            errors.append(f"Segment {i}: start_time ({start}) >= end_time ({end})")
        
        # Check sequence with previous segment
        if i > 0:
            prev_end = segments[i-1].get(end_key, 0)
            if start < prev_end:
                errors.append(f"Segment {i}: overlaps with previous (start: {start}, prev_end: {prev_end})")
    
    return errors


def calculate_coverage_statistics(segments: List[Dict[str, Any]], 
                                 total_duration: float) -> Dict[str, float]:
    """
    Calculate coverage statistics for segments
    
    Args:
        segments: List of segments with start_time and end_time
        total_duration: Total duration of the video
        
    Returns:
        Dictionary with coverage statistics
    """
    if not segments or total_duration <= 0:
        return {
            "coverage_percentage": 0.0,
            "total_segment_duration": 0.0,
            "average_segment_duration": 0.0,
            "gaps_duration": total_duration,
            "gaps_percentage": 100.0
        }
    
    # Calculate total covered time
    covered_time = 0
    for segment in segments:
        start = segment.get('start_time', 0)
        end = segment.get('end_time', 0)
        covered_time += max(0, end - start)
    
    # Calculate statistics
    coverage_pct = (covered_time / total_duration) * 100
    avg_duration = covered_time / len(segments) if segments else 0
    gaps_duration = total_duration - covered_time
    gaps_pct = (gaps_duration / total_duration) * 100
    
    return {
        "coverage_percentage": round(coverage_pct, 2),
        "total_segment_duration": round(covered_time, 2),
        "average_segment_duration": round(avg_duration, 2),
        "gaps_duration": round(gaps_duration, 2),
        "gaps_percentage": round(gaps_pct, 2),
        "num_segments": len(segments)
    }


def create_summary_report(captions: List[Dict[str, Any]], 
                         metadata: Dict[str, Any]) -> str:
    """
    Create a human-readable summary report
    
    Args:
        captions: List of generated captions
        metadata: Pipeline metadata
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE CAPTIONING SUMMARY REPORT")
    report.append("=" * 80)
    
    # Metadata
    report.append(f"\nGenerated: {metadata.get('generated_at', 'Unknown')}")
    report.append(f"Pipeline Version: {metadata.get('pipeline_version', '0.1.0')}")
    
    # Statistics
    total_scenes = len(captions)
    successful = sum(1 for c in captions if 'error' not in c)
    failed = total_scenes - successful
    
    report.append(f"\nTotal Scenes: {total_scenes}")
    report.append(f"Successful Captions: {successful} ({successful/total_scenes*100:.1f}%)")
    report.append(f"Failed Captions: {failed} ({failed/total_scenes*100:.1f}%)")
    
    # Coverage
    if metadata.get('total_duration'):
        coverage_stats = calculate_coverage_statistics(
            captions, metadata['total_duration']
        )
        report.append(f"\nCoverage: {coverage_stats['coverage_percentage']}%")
        report.append(f"Total Caption Duration: {format_seconds_readable(coverage_stats['total_segment_duration'])}")
        report.append(f"Average Caption Duration: {format_seconds_readable(coverage_stats['average_segment_duration'])}")
    
    # Character statistics
    all_characters = set()
    dialogue_scenes = 0
    for caption in captions:
        if caption.get('characters'):
            all_characters.update(caption['characters'])
        if caption.get('has_dialogue'):
            dialogue_scenes += 1
    
    report.append(f"\nUnique Characters: {len(all_characters)}")
    report.append(f"Scenes with Dialogue: {dialogue_scenes} ({dialogue_scenes/total_scenes*100:.1f}%)")
    
    # Sample captions
    report.append("\nSAMPLE CAPTIONS:")
    report.append("-" * 40)
    
    for caption in captions[:3]:  # First 3 captions
        report.append(f"\nScene {caption.get('scene_id', 'Unknown')}: {format_time_range(caption.get('start_time', 0), caption.get('end_time', 0))}")
        if caption.get('characters'):
            report.append(f"Characters: {', '.join(caption['characters'])}")
        report.append(f"Caption: {caption.get('caption', '[No caption]')}")
    
    if len(captions) > 3:
        report.append(f"\n... and {len(captions) - 3} more scenes")
    
    report.append("\n" + "=" * 80)
    
    return '\n'.join(report)


if __name__ == "__main__":
    # Test utilities
    
    # Test time formatting
    print("Time Formatting Tests:")
    test_time = 3665.123  # 1:01:05.123
    print(f"  Readable: {format_seconds_readable(test_time)}")
    print(f"  SRT: {format_seconds_srt(test_time)}")
    print(f"  WebVTT: {format_seconds_webvtt(test_time)}")
    print(f"  Compact: {format_seconds_compact(test_time)}")
    
    # Test time range
    print(f"\nTime Range: {format_time_range(100, 200, 'readable')}")
    
    # Test segment merging
    segments = [
        {"start_time": 0, "end_time": 10, "text": "Hello"},
        {"start_time": 10.1, "end_time": 20, "text": "World"},
        {"start_time": 30, "end_time": 40, "text": "Test"}
    ]
    merged = merge_overlapping_segments(segments)
    print(f"\nMerged Segments: {len(segments)} -> {len(merged)}")
    
    # Test coverage statistics
    stats = calculate_coverage_statistics(segments, 60)
    print(f"\nCoverage Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")