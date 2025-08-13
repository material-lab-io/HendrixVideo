"""
Robust Frame Extraction System with Multi-Level Fallback

This module implements a comprehensive frame extraction system that adapts
to any video quality and ensures adequate coverage for character detection.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import logging
from pathlib import Path
import json
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class FrameExtractionStrategy:
    """Defines a frame extraction strategy with parameters"""
    name: str
    quality_threshold: float
    motion_threshold: float
    min_frames_per_second: float
    max_frames_per_second: float
    priority: int  # Lower is higher priority
    
    
@dataclass
class ExtractionResult:
    """Results from frame extraction attempt"""
    frames: List[Dict[str, Any]]
    strategy_used: str
    quality_stats: Dict[str, float]
    coverage_stats: Dict[str, float]
    

class RobustFrameExtractor:
    """Multi-level frame extraction with intelligent fallback strategies"""
    
    # Define extraction strategies in order of preference
    STRATEGIES = [
        FrameExtractionStrategy(
            name="medium_quality",
            quality_threshold=0.15,  # Lowered from 0.2
            motion_threshold=5.0,    # Lowered from 10.0
            min_frames_per_second=2.0,
            max_frames_per_second=5.0,
            priority=1
        ),
        FrameExtractionStrategy(
            name="low_quality",
            quality_threshold=0.05,
            motion_threshold=2.0,    # Lowered from 5.0
            min_frames_per_second=1.5,
            max_frames_per_second=3.0,
            priority=2
        ),
        FrameExtractionStrategy(
            name="force_extract",
            quality_threshold=-1.0,  # Accept any frame
            motion_threshold=0.0,
            min_frames_per_second=1.0,
            max_frames_per_second=2.0,
            priority=3
        )
    ]
    
    def __init__(self, target_coverage: float = 0.8, min_frames: int = 100):
        """
        Args:
            target_coverage: Target percentage of video duration to cover (0-1)
            min_frames: Minimum number of frames to extract
        """
        self.target_coverage = target_coverage
        self.min_frames = min_frames
        self.frame_cache = {}
        
    def extract_frames_adaptive(self,
                              video_path: str,
                              dialogue_segments: List[Dict],
                              output_dir: Optional[str] = None) -> ExtractionResult:
        """Extract frames with multi-level fallback strategy
        
        Args:
            video_path: Path to video file
            dialogue_segments: List of dialogue timing information
            output_dir: Optional directory to save frames
            
        Returns:
            ExtractionResult with frames and statistics
        """
        logger.info(f"Starting robust frame extraction for: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video: {total_frames} frames, {fps:.2f} fps, {duration:.1f}s")
        
        # Try strategies in order until we get adequate coverage
        for strategy in self.STRATEGIES:
            logger.info(f"Trying strategy: {strategy.name}")
            
            result = self._extract_with_strategy(
                cap, strategy, dialogue_segments, 
                fps, duration, total_frames, output_dir
            )
            
            # Check if we have adequate coverage
            coverage = self._calculate_coverage(result.frames, duration)
            logger.info(f"Strategy {strategy.name}: {len(result.frames)} frames, "
                       f"{coverage:.1%} coverage")
            
            if len(result.frames) >= self.min_frames and coverage >= self.target_coverage:
                logger.info(f"Adequate coverage achieved with {strategy.name}")
                cap.release()
                return result
            
            # Reset video for next attempt
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # If we get here, use the best result we got
        cap.release()
        logger.warning(f"Could not achieve target coverage, using best result")
        return result
    
    def _extract_with_strategy(self,
                             cap,
                             strategy: FrameExtractionStrategy,
                             dialogue_segments: List[Dict],
                             fps: float,
                             duration: float,
                             total_frames: int,
                             output_dir: Optional[str]) -> ExtractionResult:
        """Extract frames using a specific strategy"""
        
        # Calculate frame schedule based on dialogue timing
        frame_schedule = self._calculate_adaptive_schedule(
            dialogue_segments, strategy, fps, duration, total_frames
        )
        
        # Limit frame schedule for performance
        max_frames_per_strategy = min(len(frame_schedule), 2000)
        if len(frame_schedule) > max_frames_per_strategy:
            logger.info(f"Limiting frame schedule from {len(frame_schedule)} to {max_frames_per_strategy}")
            # Sample uniformly from schedule
            indices = np.linspace(0, len(frame_schedule)-1, max_frames_per_strategy, dtype=int)
            frame_schedule = [frame_schedule[i] for i in indices]
        
        # Extract frames
        extracted_frames = []
        quality_scores = []
        frames_checked = 0
        
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        prev_frame = None
        for i, frame_num in enumerate(frame_schedule):
            # Early termination if we have enough frames
            if len(extracted_frames) >= self.min_frames and \
               self._calculate_coverage(extracted_frames, duration) >= self.target_coverage:
                logger.info(f"Early termination: sufficient coverage achieved")
                break
            
            # Progress logging
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(frame_schedule)} frames checked, "
                           f"{len(extracted_frames)} extracted")
            
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            frames_checked += 1
            
            # Calculate quality metrics
            quality = self._calculate_frame_quality(frame)
            motion = 0.0
            
            if prev_frame is not None:
                motion = self._calculate_motion(prev_frame, frame)
            
            # Apply strategy filters
            if strategy.quality_threshold >= 0 and quality < strategy.quality_threshold:
                continue
                
            if strategy.motion_threshold > 0 and motion < strategy.motion_threshold:
                continue
            
            # Frame passed filters
            timestamp = frame_num / fps
            frame_data = {
                'frame_number': frame_num,
                'timestamp': timestamp,
                'quality_score': quality,
                'motion_score': motion,
                'width': frame.shape[1],
                'height': frame.shape[0]
            }
            
            # Save or store frame
            if output_dir:
                frame_path = Path(output_dir) / f"frame_{frame_num:08d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                frame_data['path'] = str(frame_path)
            else:
                frame_data['image'] = frame
            
            extracted_frames.append(frame_data)
            quality_scores.append(quality)
            prev_frame = frame.copy()
        
        logger.info(f"Strategy {strategy.name}: checked {frames_checked} frames, "
                   f"extracted {len(extracted_frames)}")
        
        # Calculate statistics
        quality_stats = {
            'mean': np.mean(quality_scores) if quality_scores else 0,
            'std': np.std(quality_scores) if quality_scores else 0,
            'min': np.min(quality_scores) if quality_scores else 0,
            'max': np.max(quality_scores) if quality_scores else 0
        }
        
        coverage_stats = {
            'temporal_coverage': self._calculate_coverage(extracted_frames, duration),
            'dialogue_coverage': self._calculate_dialogue_coverage(
                extracted_frames, dialogue_segments
            )
        }
        
        return ExtractionResult(
            frames=extracted_frames,
            strategy_used=strategy.name,
            quality_stats=quality_stats,
            coverage_stats=coverage_stats
        )
    
    def _calculate_adaptive_schedule(self,
                                   dialogue_segments: List[Dict],
                                   strategy: FrameExtractionStrategy,
                                   fps: float,
                                   duration: float,
                                   total_frames: int) -> List[int]:
        """Calculate frame extraction schedule based on dialogue and strategy"""
        
        # Create density map
        time_resolution = 0.1
        time_buckets = int(duration / time_resolution) + 1
        
        # Base density
        base_density = strategy.min_frames_per_second * time_resolution
        frame_density = np.ones(time_buckets) * base_density
        
        # Increase density during dialogue
        dialogue_density = strategy.max_frames_per_second * time_resolution
        
        for segment in dialogue_segments:
            start_time = max(0, segment.get('start_time', 0) - 2.0)
            end_time = min(duration, segment.get('end_time', 0) + 2.0)
            
            start_bucket = int(start_time / time_resolution)
            end_bucket = min(int(end_time / time_resolution) + 1, time_buckets)
            
            frame_density[start_bucket:end_bucket] = dialogue_density
        
        # Add scene change detection points
        scene_changes = self._detect_scene_changes_fast(total_frames, fps)
        for scene_time in scene_changes:
            bucket = int(scene_time / time_resolution)
            if 0 <= bucket < time_buckets:
                frame_density[bucket] = max(frame_density[bucket], dialogue_density)
        
        # Convert to frame numbers
        frame_schedule = []
        cumulative = 0.0
        
        for bucket_idx, density in enumerate(frame_density):
            time_point = bucket_idx * time_resolution
            cumulative += density
            
            while cumulative >= 1.0 and len(frame_schedule) < total_frames:
                frame_num = int(time_point * fps)
                if 0 <= frame_num < total_frames:
                    frame_schedule.append(frame_num)
                cumulative -= 1.0
        
        # Remove duplicates and sort
        frame_schedule = sorted(list(set(frame_schedule)))
        
        # Ensure minimum coverage by adding uniform samples if needed
        if len(frame_schedule) < self.min_frames:
            additional_needed = self.min_frames - len(frame_schedule)
            step = max(1, total_frames // additional_needed)
            
            for i in range(0, total_frames, step):
                if i not in frame_schedule:
                    frame_schedule.append(i)
                if len(frame_schedule) >= self.min_frames:
                    break
        
        return sorted(frame_schedule)
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """Calculate comprehensive frame quality score (optimized)"""
        # Downsample for faster processing
        if frame.shape[0] > 360:
            scale = 360 / frame.shape[0]
            new_size = (int(frame.shape[1] * scale), int(frame.shape[0] * scale))
            frame_small = cv2.resize(frame, new_size)
        else:
            frame_small = frame
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        
        # Simplified quality metrics for speed
        
        # 1. Laplacian variance (blur detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(1.0, laplacian_var / 200.0)  # Adjusted threshold
        
        # 2. Contrast (standard deviation)
        contrast_score = min(1.0, gray.std() / 50.0)  # Adjusted threshold
        
        # 3. Simple brightness check
        mean_brightness = gray.mean()
        brightness_ok = 30 < mean_brightness < 225  # Not too dark or bright
        brightness_score = 1.0 if brightness_ok else 0.5
        
        # Weighted average (simplified)
        quality_score = blur_score * 0.5 + contrast_score * 0.3 + brightness_score * 0.2
        
        return quality_score
    
    def _calculate_motion(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """Calculate motion between frames"""
        # Convert to grayscale
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(prev_gray, curr_gray)
        
        # Motion score
        motion_score = diff.mean()
        
        return motion_score
    
    def _detect_scene_changes_fast(self, total_frames: int, fps: float) -> List[float]:
        """Fast scene change detection using frame sampling"""
        # Sample every 2 seconds for scene detection
        sample_interval = int(fps * 2)
        scene_times = []
        
        # Add some heuristic scene change points
        # Typically scenes change every 3-10 seconds
        avg_scene_duration = 5.0
        num_scenes = int(total_frames / fps / avg_scene_duration)
        
        for i in range(num_scenes):
            scene_time = i * avg_scene_duration + np.random.uniform(-1, 1)
            if 0 <= scene_time <= total_frames / fps:
                scene_times.append(scene_time)
        
        return scene_times
    
    def _calculate_coverage(self, frames: List[Dict], duration: float) -> float:
        """Calculate temporal coverage of extracted frames"""
        if not frames or duration <= 0:
            return 0.0
        
        # Create time bins
        bin_size = 1.0  # 1 second bins
        num_bins = int(duration / bin_size) + 1
        covered_bins = set()
        
        for frame in frames:
            bin_idx = int(frame['timestamp'] / bin_size)
            covered_bins.add(bin_idx)
        
        coverage = len(covered_bins) / num_bins
        return coverage
    
    def _calculate_dialogue_coverage(self, 
                                   frames: List[Dict], 
                                   dialogue_segments: List[Dict]) -> float:
        """Calculate how well frames cover dialogue segments"""
        if not dialogue_segments:
            return 1.0
        
        covered_segments = 0
        
        for segment in dialogue_segments:
            start = segment.get('start_time', 0)
            end = segment.get('end_time', 0)
            
            # Check if any frame falls within or near the segment
            buffer = 2.0  # 2 second buffer
            for frame in frames:
                if start - buffer <= frame['timestamp'] <= end + buffer:
                    covered_segments += 1
                    break
        
        coverage = covered_segments / len(dialogue_segments)
        return coverage
    
    def extract_gap_filling_frames(self,
                                 video_path: str,
                                 existing_frames: List[Dict],
                                 target_gaps: List[Tuple[float, float]],
                                 frames_per_gap: int = 10) -> List[Dict]:
        """Extract additional frames to fill temporal gaps
        
        Args:
            video_path: Path to video
            existing_frames: Already extracted frames
            target_gaps: List of (start_time, end_time) gaps to fill
            frames_per_gap: Number of frames to extract per gap
            
        Returns:
            List of additional frames
        """
        logger.info(f"Filling {len(target_gaps)} temporal gaps")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        additional_frames = []
        
        for gap_start, gap_end in target_gaps:
            gap_duration = gap_end - gap_start
            
            if gap_duration <= 0:
                continue
            
            # Calculate frame positions within gap
            frame_times = np.linspace(gap_start, gap_end, frames_per_gap)
            
            for time_point in frame_times:
                frame_num = int(time_point * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                
                ret, frame = cap.read()
                if not ret:
                    continue
                
                frame_data = {
                    'frame_number': frame_num,
                    'timestamp': time_point,
                    'quality_score': self._calculate_frame_quality(frame),
                    'image': frame,
                    'gap_fill': True
                }
                
                additional_frames.append(frame_data)
        
        cap.release()
        logger.info(f"Extracted {len(additional_frames)} gap-filling frames")
        
        return additional_frames