"""
DeepFace Attribute Analyzer

This module provides face attribute analysis using DeepFace,
extracting age, gender, emotion, race, and other characteristics.
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path
import json

# Set environment variable for tf_keras before importing deepface
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

try:
    from deepface import DeepFace
except ImportError:
    raise ImportError("DeepFace not installed. Run: pip install deepface tf_keras")

logger = logging.getLogger(__name__)


@dataclass
class FaceAttributes:
    """Face attributes extracted by DeepFace"""
    age: int
    gender: str
    gender_confidence: float
    dominant_emotion: str
    emotion_scores: Dict[str, float]
    dominant_race: str
    race_scores: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'age': int(self.age),
            'gender': self.gender,
            'gender_confidence': float(self.gender_confidence),
            'dominant_emotion': self.dominant_emotion,
            'emotion_scores': {k: float(v) for k, v in self.emotion_scores.items()},
            'dominant_race': self.dominant_race,
            'race_scores': {k: float(v) for k, v in self.race_scores.items()}
        }


@dataclass
class AttributeAnalysis:
    """Complete attribute analysis for a face"""
    face_bbox: Tuple[int, int, int, int]
    frame_number: int
    timestamp: float
    attributes: FaceAttributes
    confidence: float
    

@dataclass
class DeepFaceConfig:
    """Configuration for DeepFace analyzer"""
    actions: List[str] = None  # ['age', 'gender', 'emotion', 'race']
    enforce_detection: bool = False  # Don't fail if face not detected
    detector_backend: str = 'opencv'  # Fast backend
    align: bool = True  # Face alignment
    silent: bool = True  # Suppress DeepFace output
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = ['age', 'gender', 'emotion', 'race']


class DeepFaceAnalyzer:
    """Analyzes face attributes using DeepFace"""
    
    def __init__(self, config: DeepFaceConfig = None):
        """Initialize DeepFace analyzer"""
        self.config = config or DeepFaceConfig()
        self._initialize_models()
        
        # Track analysis statistics
        self.analysis_stats = {
            'attempted': 0,
            'successful': 0,
            'failed_reasons': {}
        }
        
    def _initialize_models(self):
        """Pre-load models to avoid repeated loading"""
        logger.info("Initializing DeepFace models...")
        
        # This will download and cache models on first use
        try:
            # Dummy analysis to load models
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            dummy_img[30:70, 30:70] = 255  # White square as "face"
            
            _ = DeepFace.analyze(
                dummy_img,
                actions=self.config.actions,
                enforce_detection=False,
                detector_backend=self.config.detector_backend,
                silent=True
            )
            logger.info("DeepFace models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Model initialization warning: {e}")
    
    def analyze_face(self, face_image: np.ndarray) -> Optional[FaceAttributes]:
        """Analyze a single face image
        
        Args:
            face_image: Face image (BGR format)
            
        Returns:
            FaceAttributes or None if analysis fails
        """
        self.analysis_stats['attempted'] += 1
        
        try:
            # Ensure minimum size
            h, w = face_image.shape[:2]
            if h < 48 or w < 48:
                # Upscale small faces
                scale = max(48/h, 48/w)
                new_h, new_w = int(h * scale), int(w * scale)
                face_image = cv2.resize(face_image, (new_w, new_h), 
                                      interpolation=cv2.INTER_CUBIC)
            
            # Run DeepFace analysis
            results = DeepFace.analyze(
                face_image,
                actions=self.config.actions,
                enforce_detection=self.config.enforce_detection,
                detector_backend=self.config.detector_backend,
                align=self.config.align,
                silent=self.config.silent
            )
            
            # Handle both single dict and list of dicts
            if isinstance(results, list):
                result = results[0]
            else:
                result = results
            
            # Extract attributes
            attributes = FaceAttributes(
                age=int(result.get('age', 0)),
                gender=result.get('dominant_gender', 'unknown'),
                gender_confidence=result.get('gender', {}).get(
                    result.get('dominant_gender', 'Man'), 0.5
                ),
                dominant_emotion=result.get('dominant_emotion', 'neutral'),
                emotion_scores=result.get('emotion', {}),
                dominant_race=result.get('dominant_race', 'unknown'),
                race_scores=result.get('race', {})
            )
            
            self.analysis_stats['successful'] += 1
            return attributes
            
        except Exception as e:
            self._record_failure(str(type(e).__name__))
            logger.debug(f"Face analysis failed: {e}")
            return None
    
    def analyze_faces_in_frame(self, frame: np.ndarray, 
                              face_bboxes: List[Tuple[int, int, int, int]],
                              frame_number: int,
                              timestamp: float) -> List[AttributeAnalysis]:
        """Analyze multiple faces in a frame
        
        Args:
            frame: Full frame image
            face_bboxes: List of face bounding boxes
            frame_number: Frame number in video
            timestamp: Timestamp in seconds
            
        Returns:
            List of AttributeAnalysis objects
        """
        analyses = []
        
        for bbox in face_bboxes:
            x1, y1, x2, y2 = bbox
            
            # Extract face with padding
            pad = 10
            x1_pad = max(0, x1 - pad)
            y1_pad = max(0, y1 - pad)
            x2_pad = min(frame.shape[1], x2 + pad)
            y2_pad = min(frame.shape[0], y2 + pad)
            
            face_image = frame[y1_pad:y2_pad, x1_pad:x2_pad]
            
            # Analyze face
            attributes = self.analyze_face(face_image)
            
            if attributes:
                analysis = AttributeAnalysis(
                    face_bbox=bbox,
                    frame_number=frame_number,
                    timestamp=timestamp,
                    attributes=attributes,
                    confidence=1.0  # Could add face detection confidence here
                )
                analyses.append(analysis)
        
        return analyses
    
    def analyze_video_faces(self, video_path: str,
                           face_detections: List[Any],
                           sample_rate: int = 30,
                           progress_callback=None) -> List[AttributeAnalysis]:
        """Analyze faces throughout a video
        
        Args:
            video_path: Path to video file
            face_detections: List of face detections with bboxes
            sample_rate: Analyze every Nth detection
            progress_callback: Optional progress callback
            
        Returns:
            List of AttributeAnalysis objects
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        analyses = []
        processed_frames = set()
        total_to_process = len([d for i, d in enumerate(face_detections) 
                               if i % sample_rate == 0])
        processed_count = 0
        
        logger.info(f"Analyzing attributes for {total_to_process} face samples...")
        
        for i, detection in enumerate(face_detections):
            if i % sample_rate != 0:
                continue
            
            frame_num = detection.frame_number
            if frame_num in processed_frames:
                continue
            
            # Read frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Get face bbox
            if hasattr(detection, 'face_bbox') and detection.face_bbox:
                face_bbox = detection.face_bbox
            elif hasattr(detection, 'bbox'):
                face_bbox = detection.bbox
            else:
                continue
            
            # Analyze single face
            frame_analyses = self.analyze_faces_in_frame(
                frame, [face_bbox], frame_num, detection.timestamp
            )
            
            analyses.extend(frame_analyses)
            processed_frames.add(frame_num)
            
            processed_count += 1
            if progress_callback and processed_count % 10 == 0:
                progress_callback(processed_count / total_to_process)
            
            if len(analyses) % 10 == 0 and len(analyses) > 0:
                logger.info(f"Analyzed {len(analyses)} faces "
                          f"({len(analyses)/processed_count*100:.1f}% success rate)")
        
        cap.release()
        
        # Log statistics
        logger.info(f"Attribute analysis complete: {len(analyses)}/{self.analysis_stats['attempted']} "
                   f"({len(analyses)/self.analysis_stats['attempted']*100:.1f}% success)")
        if self.analysis_stats['failed_reasons']:
            logger.info(f"Failure reasons: {self.analysis_stats['failed_reasons']}")
        
        return analyses
    
    def _record_failure(self, reason: str):
        """Record failure reason for analysis"""
        if reason not in self.analysis_stats['failed_reasons']:
            self.analysis_stats['failed_reasons'][reason] = 0
        self.analysis_stats['failed_reasons'][reason] += 1
    
    def aggregate_character_attributes(self, 
                                     character_analyses: List[AttributeAnalysis]) -> Dict:
        """Aggregate attributes for a character across multiple frames
        
        Args:
            character_analyses: Analyses for a single character
            
        Returns:
            Aggregated attributes dictionary
        """
        if not character_analyses:
            return {}
        
        # Collect all attributes
        ages = []
        genders = {}
        emotions = {}
        races = {}
        
        for analysis in character_analyses:
            attr = analysis.attributes
            
            # Age
            ages.append(attr.age)
            
            # Gender
            if attr.gender not in genders:
                genders[attr.gender] = []
            genders[attr.gender].append(attr.gender_confidence)
            
            # Emotions
            for emotion, score in attr.emotion_scores.items():
                if emotion not in emotions:
                    emotions[emotion] = []
                emotions[emotion].append(score)
            
            # Race
            for race, score in attr.race_scores.items():
                if race not in races:
                    races[race] = []
                races[race].append(score)
        
        # Aggregate results
        aggregated = {
            'age': {
                'mean': float(np.mean(ages)),
                'median': float(np.median(ages)),
                'std': float(np.std(ages)),
                'min': int(min(ages)),
                'max': int(max(ages))
            },
            'gender': {
                gender: {
                    'frequency': len(scores) / len(character_analyses),
                    'avg_confidence': float(np.mean(scores))
                }
                for gender, scores in genders.items()
            },
            'emotions': {
                emotion: {
                    'avg_score': float(np.mean(scores)),
                    'max_score': float(max(scores)),
                    'frequency': sum(s > 0.1 for s in scores) / len(character_analyses)
                }
                for emotion, scores in emotions.items()
            },
            'race': {
                race: {
                    'avg_score': float(np.mean(scores)),
                    'frequency': len(scores) / len(character_analyses)
                }
                for race, scores in races.items()
            },
            'num_analyses': len(character_analyses)
        }
        
        # Determine dominant attributes
        aggregated['dominant_gender'] = max(genders.keys(), 
                                          key=lambda g: len(genders[g]))
        aggregated['dominant_emotion'] = max(emotions.keys(),
                                           key=lambda e: np.mean(emotions[e]))
        aggregated['dominant_race'] = max(races.keys(),
                                        key=lambda r: np.mean(races[r]))
        
        return aggregated