"""
Intelligent Frame Extraction and Preprocessing

This module extracts key frames from videos and preprocesses them
for improved face detection and embedding extraction.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFrame:
    """Represents an extracted frame with metadata"""
    frame_number: int
    timestamp: float
    image: np.ndarray
    quality_score: float
    is_keyframe: bool
    scene_change_score: float
    hash: str  # For duplicate detection
    
    def save(self, path: str):
        """Save frame to disk"""
        cv2.imwrite(path, self.image)


@dataclass
class FrameExtractionConfig:
    """Configuration for frame extraction"""
    extraction_mode: str = "intelligent"  # intelligent, uniform, scene_change
    target_frames: int = 100  # Target number of frames to extract
    quality_threshold: float = 0.7  # Minimum quality score
    scene_threshold: float = 30.0  # Scene change threshold
    blur_threshold: float = 100.0  # Laplacian variance threshold
    save_frames: bool = True  # Save extracted frames to disk
    frame_dir: str = "extracted_frames"  # Directory for saved frames
    resize_width: int = 1920  # Resize frames to this width (maintain aspect)
    enhance_quality: bool = True  # Apply enhancement to frames
    detect_duplicates: bool = True  # Skip duplicate/similar frames
    parallel_workers: int = 4  # Number of parallel workers


class FrameExtractor:
    """Intelligent frame extraction from videos"""
    
    def __init__(self, config: FrameExtractionConfig = None):
        self.config = config or FrameExtractionConfig()
        self.frame_hashes = set()  # For duplicate detection
        
    def extract_frames(self, video_path: str, output_dir: Optional[str] = None) -> List[ExtractedFrame]:
        """Extract key frames from video using intelligent selection
        
        Args:
            video_path: Path to video file
            output_dir: Optional directory to save frames
            
        Returns:
            List of ExtractedFrame objects
        """
        logger.info(f"Extracting frames from: {video_path}")
        
        # Get video info
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video info: {total_frames} frames, {fps:.2f} fps, {duration:.1f}s")
        
        # Choose extraction strategy
        if self.config.extraction_mode == "intelligent":
            frames = self._intelligent_extraction(cap, fps, total_frames)
        elif self.config.extraction_mode == "scene_change":
            frames = self._scene_change_extraction(cap, fps, total_frames)
        else:  # uniform
            frames = self._uniform_extraction(cap, fps, total_frames)
        
        cap.release()
        
        # Save frames if requested
        if self.config.save_frames and output_dir:
            self._save_frames(frames, output_dir)
        
        logger.info(f"Extracted {len(frames)} key frames")
        return frames
    
    def _intelligent_extraction(self, cap, fps: float, total_frames: int) -> List[ExtractedFrame]:
        """Extract frames using intelligent selection based on quality and content"""
        frames = []
        
        # Calculate sampling interval
        interval = max(1, total_frames // (self.config.target_frames * 3))  # Oversample for selection
        
        prev_frame = None
        frame_candidates = []
        
        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Calculate quality metrics
            quality_score = self._calculate_frame_quality(frame)
            scene_change = 0.0
            
            if prev_frame is not None:
                scene_change = self._calculate_scene_change(prev_frame, frame)
            
            # Check for duplicates
            if self.config.detect_duplicates:
                frame_hash = self._calculate_frame_hash(frame)
                if frame_hash in self.frame_hashes:
                    continue
                self.frame_hashes.add(frame_hash)
            
            # Create frame object
            extracted = ExtractedFrame(
                frame_number=i,
                timestamp=i / fps,
                image=frame,
                quality_score=quality_score,
                is_keyframe=scene_change > self.config.scene_threshold,
                scene_change_score=scene_change,
                hash=frame_hash if self.config.detect_duplicates else ""
            )
            
            frame_candidates.append(extracted)
            prev_frame = frame
        
        # Select best frames
        frames = self._select_best_frames(frame_candidates)
        
        # Enhance frames if enabled
        if self.config.enhance_quality:
            frames = self._enhance_frames(frames)
        
        return frames
    
    def _scene_change_extraction(self, cap, fps: float, total_frames: int) -> List[ExtractedFrame]:
        """Extract frames at scene changes"""
        frames = []
        prev_frame = None
        
        # Sample every N frames for scene detection
        sample_interval = max(1, int(fps / 5))  # 5 samples per second
        
        for i in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            if prev_frame is not None:
                scene_change = self._calculate_scene_change(prev_frame, frame)
                
                if scene_change > self.config.scene_threshold:
                    # Scene change detected, extract high-quality frame
                    best_frame = self._extract_best_frame_around(cap, i, fps)
                    if best_frame:
                        frames.append(best_frame)
            
            prev_frame = frame
        
        return frames
    
    def _uniform_extraction(self, cap, fps: float, total_frames: int) -> List[ExtractedFrame]:
        """Extract frames at uniform intervals"""
        frames = []
        interval = max(1, total_frames // self.config.target_frames)
        
        for i in range(0, total_frames, interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            quality_score = self._calculate_frame_quality(frame)
            
            extracted = ExtractedFrame(
                frame_number=i,
                timestamp=i / fps,
                image=frame,
                quality_score=quality_score,
                is_keyframe=False,
                scene_change_score=0.0,
                hash=""
            )
            
            frames.append(extracted)
        
        return frames
    
    def _calculate_frame_quality(self, frame: np.ndarray) -> float:
        """Calculate overall frame quality score"""
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Blur detection (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(1.0, laplacian_var / self.config.blur_threshold)
        
        # 2. Contrast score
        contrast = gray.std() / 255.0
        
        # 3. Brightness score (not too dark, not too bright)
        brightness = gray.mean() / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2
        
        # 4. Edge density (more edges = more detail)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        edge_score = min(1.0, edge_density * 10)
        
        # Combine scores
        quality = (
            blur_score * 0.4 +
            contrast * 0.2 +
            brightness_score * 0.2 +
            edge_score * 0.2
        )
        
        return float(quality)
    
    def _calculate_scene_change(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calculate scene change score between two frames"""
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Resize for faster computation
        small1 = cv2.resize(gray1, (160, 90))
        small2 = cv2.resize(gray2, (160, 90))
        
        # Calculate histogram difference
        hist1 = cv2.calcHist([small1], [0], None, [64], [0, 256])
        hist2 = cv2.calcHist([small2], [0], None, [64], [0, 256])
        
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        hist_diff = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
        
        # Calculate pixel difference
        diff = cv2.absdiff(small1, small2)
        pixel_diff = np.mean(diff)
        
        # Combine metrics
        scene_change = hist_diff * 0.5 + pixel_diff * 0.5
        
        return float(scene_change)
    
    def _calculate_frame_hash(self, frame: np.ndarray) -> str:
        """Calculate perceptual hash for duplicate detection"""
        # Resize to 8x8
        small = cv2.resize(frame, (8, 8))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Calculate average
        avg = gray.mean()
        
        # Create binary hash
        hash_bits = (gray > avg).flatten()
        hash_str = ''.join(['1' if b else '0' for b in hash_bits])
        
        return hashlib.md5(hash_str.encode()).hexdigest()[:16]
    
    def _select_best_frames(self, candidates: List[ExtractedFrame]) -> List[ExtractedFrame]:
        """Select best frames from candidates"""
        # Sort by quality score
        candidates.sort(key=lambda f: f.quality_score, reverse=True)
        
        # Always include keyframes (scene changes)
        keyframes = [f for f in candidates if f.is_keyframe]
        regular_frames = [f for f in candidates if not f.is_keyframe]
        
        # Select frames with temporal diversity
        selected = keyframes[:self.config.target_frames // 2]
        
        # Add high-quality regular frames
        remaining_slots = self.config.target_frames - len(selected)
        
        # Ensure temporal distribution
        if regular_frames and remaining_slots > 0:
            # Sort by timestamp
            regular_frames.sort(key=lambda f: f.timestamp)
            
            # Select evenly distributed frames
            interval = max(1, len(regular_frames) // remaining_slots)
            for i in range(0, len(regular_frames), interval):
                if len(selected) < self.config.target_frames:
                    selected.append(regular_frames[i])
        
        # Sort by timestamp for sequential processing
        selected.sort(key=lambda f: f.timestamp)
        
        return selected
    
    def _extract_best_frame_around(self, cap, center_frame: int, fps: float,
                                  window: int = 10) -> Optional[ExtractedFrame]:
        """Extract best quality frame around a center point"""
        best_frame = None
        best_quality = 0.0
        
        for offset in range(-window//2, window//2 + 1):
            frame_num = center_frame + offset
            if frame_num < 0:
                continue
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            quality = self._calculate_frame_quality(frame)
            
            if quality > best_quality:
                best_quality = quality
                best_frame = ExtractedFrame(
                    frame_number=frame_num,
                    timestamp=frame_num / fps,
                    image=frame,
                    quality_score=quality,
                    is_keyframe=True,
                    scene_change_score=0.0,
                    hash=""
                )
        
        return best_frame
    
    def _enhance_frames(self, frames: List[ExtractedFrame]) -> List[ExtractedFrame]:
        """Enhance frame quality for better detection"""
        enhanced_frames = []
        
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            future_to_frame = {
                executor.submit(self._enhance_single_frame, frame): frame
                for frame in frames
            }
            
            for future in as_completed(future_to_frame):
                enhanced_frame = future.result()
                if enhanced_frame:
                    enhanced_frames.append(enhanced_frame)
        
        # Sort by timestamp
        enhanced_frames.sort(key=lambda f: f.timestamp)
        
        return enhanced_frames
    
    def _enhance_single_frame(self, frame: ExtractedFrame) -> ExtractedFrame:
        """Enhance a single frame"""
        try:
            enhanced_img = frame.image.copy()
            
            # 1. Denoise
            enhanced_img = cv2.fastNlMeansDenoisingColored(enhanced_img, None, 10, 10, 7, 21)
            
            # 2. Adjust contrast and brightness
            lab = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            enhanced_img = cv2.merge([l, a, b])
            enhanced_img = cv2.cvtColor(enhanced_img, cv2.COLOR_LAB2BGR)
            
            # 3. Sharpen
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]]) / 1.0
            enhanced_img = cv2.filter2D(enhanced_img, -1, kernel)
            
            # Update frame
            frame.image = enhanced_img
            frame.quality_score = self._calculate_frame_quality(enhanced_img)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error enhancing frame: {e}")
            return frame
    
    def _save_frames(self, frames: List[ExtractedFrame], output_dir: str):
        """Save extracted frames to disk"""
        frame_dir = Path(output_dir) / self.config.frame_dir
        frame_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving {len(frames)} frames to: {frame_dir}")
        
        for i, frame in enumerate(frames):
            filename = f"frame_{i:04d}_t{frame.timestamp:.1f}s_q{frame.quality_score:.2f}.jpg"
            frame_path = frame_dir / filename
            
            # Resize if needed
            if self.config.resize_width and frame.image.shape[1] > self.config.resize_width:
                height = int(frame.image.shape[0] * self.config.resize_width / frame.image.shape[1])
                resized = cv2.resize(frame.image, (self.config.resize_width, height))
                cv2.imwrite(str(frame_path), resized, [cv2.IMWRITE_JPEG_QUALITY, 95])
            else:
                cv2.imwrite(str(frame_path), frame.image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Save metadata
        metadata = {
            'num_frames': len(frames),
            'extraction_config': self.config.__dict__,
            'frames': [
                {
                    'index': i,
                    'frame_number': f.frame_number,
                    'timestamp': f.timestamp,
                    'quality_score': f.quality_score,
                    'is_keyframe': f.is_keyframe,
                    'scene_change_score': f.scene_change_score
                }
                for i, f in enumerate(frames)
            ]
        }
        
        import json
        with open(frame_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)