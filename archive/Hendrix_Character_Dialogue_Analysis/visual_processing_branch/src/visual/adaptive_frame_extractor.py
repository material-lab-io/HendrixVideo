"""
Adaptive Frame Extraction with Dialogue Awareness

This module implements intelligent frame extraction that adapts to dialogue timing,
ensuring better coverage during speech segments for improved character-dialogue matching.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DialogueSegment:
    """Represents a dialogue segment for frame extraction guidance"""
    start_time: float
    end_time: float
    importance: float = 1.0  # Weight for frame allocation
    text: Optional[str] = None
    speaker_id: Optional[str] = None


@dataclass
class AdaptiveExtractionConfig:
    """Configuration for adaptive frame extraction"""
    # Base extraction parameters
    base_fps: float = 1.0  # Base frames per second for non-dialogue
    dialogue_fps: float = 5.0  # Enhanced fps during dialogue
    pre_dialogue_buffer: float = 2.0  # Seconds before dialogue to capture
    post_dialogue_buffer: float = 2.0  # Seconds after dialogue to capture
    
    # Frame allocation
    min_frames_per_segment: int = 5  # Minimum frames per dialogue segment
    max_frames_per_segment: int = 50  # Maximum frames per dialogue segment
    total_frame_budget: int = 1000  # Total frames to extract
    
    # Quality and deduplication
    quality_threshold: float = 0.3  # Minimum frame quality (blur detection)
    similarity_threshold: float = 0.95  # Threshold for duplicate detection
    
    # Optimization
    prioritize_multi_speaker: bool = True  # Extra frames for multi-speaker scenes
    detect_scene_changes: bool = True  # Include frames at scene changes
    
    def to_dict(self):
        return {
            'base_fps': self.base_fps,
            'dialogue_fps': self.dialogue_fps,
            'pre_dialogue_buffer': self.pre_dialogue_buffer,
            'post_dialogue_buffer': self.post_dialogue_buffer,
            'min_frames_per_segment': self.min_frames_per_segment,
            'max_frames_per_segment': self.max_frames_per_segment,
            'total_frame_budget': self.total_frame_budget
        }


class AdaptiveFrameExtractor:
    """Adaptive frame extraction based on dialogue timing and video characteristics"""
    
    def __init__(self, config: Optional[AdaptiveExtractionConfig] = None):
        self.config = config or AdaptiveExtractionConfig()
        self.frame_quality_cache = {}
        
    def extract_frames_with_dialogue(self, 
                                   video_path: str,
                                   dialogue_segments: List[DialogueSegment],
                                   output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract frames adaptively based on dialogue timing
        
        Args:
            video_path: Path to video file
            dialogue_segments: List of dialogue segments with timing
            output_dir: Optional directory to save extracted frames
            
        Returns:
            List of frame dictionaries with metadata
        """
        logger.info(f"Starting adaptive frame extraction for: {video_path}")
        logger.info(f"Processing {len(dialogue_segments)} dialogue segments")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video: {total_frames} frames, {fps:.2f} fps, {duration:.1f}s")
        
        # Calculate frame allocation
        frame_schedule = self._calculate_frame_schedule(
            dialogue_segments, duration, fps, total_frames
        )
        
        # Extract frames according to schedule
        extracted_frames = self._extract_scheduled_frames(
            cap, frame_schedule, fps, output_dir
        )
        
        cap.release()
        
        logger.info(f"Extracted {len(extracted_frames)} frames adaptively")
        return extracted_frames
    
    def _calculate_frame_schedule(self, 
                                dialogue_segments: List[DialogueSegment],
                                video_duration: float,
                                fps: float,
                                total_frames: int) -> List[int]:
        """Calculate which frames to extract based on dialogue timing
        
        Returns:
            List of frame numbers to extract
        """
        # Create time-based density map
        time_resolution = 0.1  # 100ms buckets
        time_buckets = int(video_duration / time_resolution) + 1
        frame_density = np.ones(time_buckets) * self.config.base_fps * time_resolution
        
        # Increase density during dialogue segments
        for segment in dialogue_segments:
            # Add buffer before and after
            start_time = max(0, segment.start_time - self.config.pre_dialogue_buffer)
            end_time = min(video_duration, segment.end_time + self.config.post_dialogue_buffer)
            
            start_bucket = int(start_time / time_resolution)
            end_bucket = min(int(end_time / time_resolution) + 1, time_buckets)
            
            # Apply dialogue frame rate
            dialogue_density = self.config.dialogue_fps * time_resolution * segment.importance
            frame_density[start_bucket:end_bucket] = np.maximum(
                frame_density[start_bucket:end_bucket],
                dialogue_density
            )
        
        # Convert density to frame numbers
        frame_schedule = []
        cumulative_frames = 0.0
        
        for bucket_idx, density in enumerate(frame_density):
            time_point = bucket_idx * time_resolution
            cumulative_frames += density
            
            while cumulative_frames >= 1.0:
                frame_num = int(time_point * fps)
                if 0 <= frame_num < total_frames:
                    frame_schedule.append(frame_num)
                cumulative_frames -= 1.0
        
        # Remove duplicates and sort
        frame_schedule = sorted(list(set(frame_schedule)))
        
        # Enforce frame budget if needed
        if len(frame_schedule) > self.config.total_frame_budget:
            # Prioritize frames during dialogue
            dialogue_frames = []
            other_frames = []
            
            for frame_num in frame_schedule:
                time_point = frame_num / fps
                is_dialogue_frame = any(
                    seg.start_time - self.config.pre_dialogue_buffer <= time_point <= 
                    seg.end_time + self.config.post_dialogue_buffer
                    for seg in dialogue_segments
                )
                
                if is_dialogue_frame:
                    dialogue_frames.append(frame_num)
                else:
                    other_frames.append(frame_num)
            
            # Keep all dialogue frames if possible
            if len(dialogue_frames) <= self.config.total_frame_budget:
                remaining_budget = self.config.total_frame_budget - len(dialogue_frames)
                # Sample other frames uniformly
                step = max(1, len(other_frames) // remaining_budget)
                sampled_other = other_frames[::step][:remaining_budget]
                frame_schedule = sorted(dialogue_frames + sampled_other)
            else:
                # Sample dialogue frames uniformly
                step = len(dialogue_frames) // self.config.total_frame_budget
                frame_schedule = sorted(dialogue_frames[::step][:self.config.total_frame_budget])
        
        logger.info(f"Scheduled {len(frame_schedule)} frames for extraction")
        return frame_schedule
    
    def _extract_scheduled_frames(self,
                                cap,
                                frame_schedule: List[int],
                                fps: float,
                                output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract frames according to schedule"""
        extracted_frames = []
        
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Process frames in order
        current_frame = 0
        schedule_idx = 0
        
        while schedule_idx < len(frame_schedule) and cap.isOpened():
            target_frame = frame_schedule[schedule_idx]
            
            # Seek to target frame if needed
            if target_frame > current_frame:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                current_frame = target_frame
            
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Failed to read frame {target_frame}")
                schedule_idx += 1
                continue
            
            # Check frame quality
            quality_score = self._calculate_frame_quality(frame)
            if quality_score < self.config.quality_threshold:
                logger.debug(f"Skipping frame {target_frame} due to low quality: {quality_score:.2f}")
                schedule_idx += 1
                current_frame += 1
                continue
            
            # Create frame metadata
            timestamp = target_frame / fps
            frame_data = {
                'frame_number': target_frame,
                'timestamp': timestamp,
                'quality_score': quality_score,
                'width': frame.shape[1],
                'height': frame.shape[0]
            }
            
            # Save frame if requested
            if output_dir:
                frame_path = Path(output_dir) / f"frame_{target_frame:08d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                frame_data['path'] = str(frame_path)
            else:
                frame_data['image'] = frame
            
            extracted_frames.append(frame_data)
            schedule_idx += 1
            current_frame += 1
            
            if schedule_idx % 100 == 0:
                logger.info(f"Extracted {schedule_idx}/{len(frame_schedule)} frames")
        
        return extracted_frames
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """Calculate frame quality score based on blur detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance (blur detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1 range
        quality_score = min(1.0, laplacian_var / 1000.0)
        
        return quality_score
    
    def analyze_video_characteristics(self, video_path: str) -> Dict[str, Any]:
        """Analyze video to determine optimal extraction parameters
        
        Returns:
            Dictionary with video characteristics and recommended settings
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Sample frames for quality analysis
        sample_size = min(100, total_frames)
        sample_interval = total_frames // sample_size
        
        quality_scores = []
        motion_scores = []
        prev_frame = None
        
        for i in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Quality analysis
            quality_scores.append(self._calculate_frame_quality(frame))
            
            # Motion analysis
            if prev_frame is not None:
                motion = cv2.absdiff(prev_frame, frame).mean()
                motion_scores.append(motion)
            
            prev_frame = frame.copy()
        
        cap.release()
        
        # Calculate statistics
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        avg_motion = np.mean(motion_scores) if motion_scores else 0
        
        # Recommend settings based on analysis
        recommendations = {
            'base_fps': 0.5 if avg_motion < 10 else 1.0,
            'dialogue_fps': 3.0 if avg_motion < 10 else 5.0,
            'quality_threshold': max(0.1, avg_quality * 0.5),
            'total_frame_budget': min(2000, int(duration * 2))  # ~2 fps average
        }
        
        return {
            'video_properties': {
                'duration': duration,
                'fps': fps,
                'resolution': f"{width}x{height}",
                'total_frames': total_frames
            },
            'quality_analysis': {
                'average_quality': avg_quality,
                'average_motion': avg_motion,
                'quality_std': np.std(quality_scores) if quality_scores else 0
            },
            'recommendations': recommendations
        }


def create_dialogue_segments_from_schema_a(schema_a_path: str) -> List[DialogueSegment]:
    """Convert Schema A transcription to dialogue segments for frame extraction"""
    with open(schema_a_path, 'r') as f:
        schema_a = json.load(f)
    
    dialogue_segments = []
    for segment in schema_a.get('segments', []):
        # Skip non-speech segments
        if segment.get('source') != 'whisper' or not segment.get('text', '').strip():
            continue
        
        # Calculate importance based on segment properties
        importance = 1.0
        
        # Longer segments are more important
        duration = segment['end_time'] - segment['start_time']
        if duration > 3.0:
            importance *= 1.2
        
        # High confidence segments are more important
        if segment.get('confidence', 0) > 0.8:
            importance *= 1.1
        
        # Emotional segments might be more important
        if segment.get('emotion') and segment['emotion'] != 'neutral':
            importance *= 1.1
        
        dialogue_segments.append(DialogueSegment(
            start_time=segment['start_time'],
            end_time=segment['end_time'],
            importance=min(2.0, importance),  # Cap at 2x
            text=segment.get('text'),
            speaker_id=segment.get('speaker_id')
        ))
    
    return dialogue_segments