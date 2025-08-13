"""
Face Tracker Module

Integrates InsightFace detection with SORT tracking to maintain consistent
character IDs across video frames.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import logging
from pathlib import Path
import json
from collections import defaultdict

from .insightface_processor import InsightFaceProcessor, ProcessedFace, InsightFaceConfig
from .sort_tracker import Sort
from .scene_detector import SceneDetector, SceneInfo

logger = logging.getLogger(__name__)


@dataclass
class TrackedFace:
    """Represents a face with tracking information"""
    track_id: int
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    embedding: np.ndarray
    landmarks: Optional[np.ndarray] = None
    frame_number: int = 0
    timestamp: float = 0.0
    detection_score: float = 0.0
    quality_score: float = 0.0
    scene_id: Optional[int] = None  # Scene this face belongs to
    
    
@dataclass 
class TrackedCharacter:
    """Represents a character tracked across the video"""
    character_id: int
    track_ids: List[int] = field(default_factory=list)  # All track IDs associated with this character
    embeddings: List[np.ndarray] = field(default_factory=list)
    representative_embedding: Optional[np.ndarray] = None
    appearances: List[TrackedFace] = field(default_factory=list)
    first_appearance: float = 0.0
    last_appearance: float = 0.0
    total_frames: int = 0
    scene_appearances: Dict[int, List[TrackedFace]] = field(default_factory=lambda: defaultdict(list))  # Appearances per scene
    scene_embeddings: Dict[int, np.ndarray] = field(default_factory=dict)  # Representative embedding per scene
    
    def update_representative_embedding(self):
        """Update the representative embedding as the mean of all embeddings"""
        if self.embeddings:
            self.representative_embedding = np.mean(self.embeddings, axis=0)
            self.representative_embedding /= np.linalg.norm(self.representative_embedding)
    
    def add_appearance(self, face: TrackedFace):
        """Add a new appearance of this character"""
        self.appearances.append(face)
        self.embeddings.append(face.embedding)
        
        if self.first_appearance == 0:
            self.first_appearance = face.timestamp
        self.last_appearance = face.timestamp
        self.total_frames += 1
        
        if face.track_id not in self.track_ids:
            self.track_ids.append(face.track_id)
        
        # Track scene-specific appearances
        if face.scene_id is not None:
            self.scene_appearances[face.scene_id].append(face)
            # Update scene-specific embedding
            scene_embeddings = [f.embedding for f in self.scene_appearances[face.scene_id]]
            self.scene_embeddings[face.scene_id] = np.mean(scene_embeddings, axis=0)
        
        # Update representative embedding periodically
        if len(self.embeddings) % 10 == 0:
            self.update_representative_embedding()


@dataclass
class FaceTrackerConfig:
    """Configuration for face tracker"""
    # InsightFace settings
    insightface_config: InsightFaceConfig = field(default_factory=InsightFaceConfig)
    
    # SORT tracking settings  
    max_age: int = 30  # Maximum frames to keep track alive without detections
    min_hits: int = 3  # Minimum detections before reporting track
    iou_threshold: float = 0.3  # Minimum IoU for matching
    use_embeddings: bool = True  # Use face embeddings for matching
    embedding_threshold: float = 0.6  # Minimum similarity for embedding matching
    
    # Character identification settings
    character_similarity_threshold: float = 0.7  # Threshold for same character
    min_character_appearances: int = 5  # Minimum appearances to be considered a character
    

class FaceTracker:
    """Tracks faces across video frames maintaining consistent IDs"""
    
    def __init__(self, config: FaceTrackerConfig = None, scene_detector: Optional[SceneDetector] = None):
        """Initialize face tracker
        
        Args:
            config: Configuration object
            scene_detector: Optional scene detector for scene-aware tracking
        """
        self.config = config or FaceTrackerConfig()
        
        # Initialize components
        self.processor = InsightFaceProcessor(self.config.insightface_config)
        self.tracker = Sort(
            max_age=self.config.max_age,
            min_hits=self.config.min_hits,
            iou_threshold=self.config.iou_threshold,
            use_embeddings=self.config.use_embeddings,
            embedding_threshold=self.config.embedding_threshold
        )
        
        # Scene detection
        self.scene_detector = scene_detector
        self.current_scene_id: Optional[int] = None
        
        # Character management
        self.characters: Dict[int, TrackedCharacter] = {}
        self.track_to_character: Dict[int, int] = {}  # Map track_id to character_id
        self.next_character_id = 1
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'tracks_created': 0,
            'characters_identified': 0
        }
    
    def process_frame(self, frame: np.ndarray, frame_number: int, 
                     timestamp: float) -> List[TrackedFace]:
        """Process a single frame and return tracked faces
        
        Args:
            frame: Video frame (BGR)
            frame_number: Frame number in video
            timestamp: Timestamp in seconds
            
        Returns:
            List of TrackedFace objects
        """
        self.stats['frames_processed'] += 1
        
        # Determine current scene if scene detector is available
        scene_id = None
        if self.scene_detector is not None and self.scene_detector.scenes:
            scene_info = self.scene_detector.get_scene_at_time(timestamp)
            if scene_info:
                scene_id = scene_info.scene_id
                if scene_id != self.current_scene_id:
                    logger.debug(f"Scene change detected: {self.current_scene_id} -> {scene_id}")
                    self.current_scene_id = scene_id
        
        # Detect faces using InsightFace
        processed_faces = self.processor.process_image(frame)
        self.stats['faces_detected'] += len(processed_faces)
        
        # Prepare detections for SORT tracker
        detections = []
        embeddings = []
        
        for face in processed_faces:
            # Convert to SORT format [x1, y1, x2, y2, score]
            x1, y1, x2, y2 = face.bbox
            detection = np.array([x1, y1, x2, y2, face.detection_score])
            detections.append(detection)
            embeddings.append(face.embedding)
        
        if len(detections) > 0:
            detections = np.array(detections)
        else:
            detections = np.empty((0, 5))
            embeddings = []
        
        # Update tracker
        tracks = self.tracker.update(detections, embeddings)
        
        # Convert tracks to TrackedFace objects
        tracked_faces = []
        
        for track in tracks:
            x1, y1, x2, y2, track_id = track.astype(int)
            
            # Find corresponding processed face
            face_idx = self._find_matching_face(
                (x1, y1, x2, y2), 
                [(f.bbox[0], f.bbox[1], f.bbox[2], f.bbox[3]) for f in processed_faces]
            )
            
            if face_idx is not None:
                face = processed_faces[face_idx]
                
                tracked_face = TrackedFace(
                    track_id=track_id,
                    bbox=(x1, y1, x2, y2),
                    embedding=face.embedding,
                    landmarks=face.landmarks,
                    frame_number=frame_number,
                    timestamp=timestamp,
                    detection_score=face.detection_score,
                    quality_score=face.quality_score,
                    scene_id=scene_id
                )
                
                tracked_faces.append(tracked_face)
                
                # Update character association
                self._update_character_association(tracked_face)
        
        return tracked_faces
    
    def _find_matching_face(self, track_bbox: Tuple, face_bboxes: List[Tuple]) -> Optional[int]:
        """Find which detected face matches the track"""
        if not face_bboxes:
            return None
            
        # Calculate IoU with all faces
        track_bbox = np.array(track_bbox)
        best_iou = 0
        best_idx = None
        
        for idx, face_bbox in enumerate(face_bboxes):
            iou = self._calculate_iou(track_bbox, np.array(face_bbox))
            if iou > best_iou:
                best_iou = iou
                best_idx = idx
        
        return best_idx if best_iou > 0.5 else None
    
    def _calculate_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """Calculate IoU between two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Calculate intersection
        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)
        
        if x_max < x_min or y_max < y_min:
            return 0.0
        
        intersection = (x_max - x_min) * (y_max - y_min)
        
        # Calculate union
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def _update_character_association(self, face: TrackedFace):
        """Update character association for a tracked face"""
        track_id = face.track_id
        
        # Check if track already associated with a character
        if track_id in self.track_to_character:
            character_id = self.track_to_character[track_id]
            self.characters[character_id].add_appearance(face)
            return
        
        # Try to match with existing characters
        best_similarity = 0
        best_character_id = None
        
        for char_id, character in self.characters.items():
            if character.representative_embedding is not None:
                similarity = self.processor.compare_embeddings(
                    face.embedding, 
                    character.representative_embedding
                )
                
                if similarity > best_similarity and similarity > self.config.character_similarity_threshold:
                    best_similarity = similarity
                    best_character_id = char_id
        
        if best_character_id is not None:
            # Associate with existing character
            self.track_to_character[track_id] = best_character_id
            self.characters[best_character_id].add_appearance(face)
        else:
            # Create new character
            character = TrackedCharacter(character_id=self.next_character_id)
            character.add_appearance(face)
            
            self.characters[self.next_character_id] = character
            self.track_to_character[track_id] = self.next_character_id
            
            self.next_character_id += 1
            self.stats['characters_identified'] += 1
    
    def process_video(self, video_path: str, sample_rate: int = 1,
                     progress_callback=None) -> Dict[int, TrackedCharacter]:
        """Process entire video and return tracked characters
        
        Args:
            video_path: Path to video file
            sample_rate: Process every Nth frame
            progress_callback: Optional callback function(frame_num, total_frames)
            
        Returns:
            Dictionary of character_id -> TrackedCharacter
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frame_number = 0
        
        logger.info(f"Processing video: {total_frames} frames at {fps} FPS")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_number % sample_rate == 0:
                timestamp = frame_number / fps
                
                # Process frame
                tracked_faces = self.process_frame(frame, frame_number, timestamp)
                
                # Progress callback
                if progress_callback:
                    progress_callback(frame_number, total_frames)
                
                # Log progress
                if frame_number % (30 * sample_rate) == 0:
                    logger.info(f"Processed {frame_number}/{total_frames} frames, "
                              f"{len(self.characters)} characters identified")
            
            frame_number += 1
        
        cap.release()
        
        # Finalize character embeddings
        for character in self.characters.values():
            character.update_representative_embedding()
        
        # Filter out characters with too few appearances
        filtered_characters = {
            char_id: char 
            for char_id, char in self.characters.items()
            if char.total_frames >= self.config.min_character_appearances
        }
        
        logger.info(f"Video processing complete. Found {len(filtered_characters)} characters")
        logger.info(f"Stats: {self.stats}")
        
        return filtered_characters
    
    def save_tracking_data(self, output_path: str):
        """Save tracking data to JSON file"""
        data = {
            'characters': {},
            'stats': self.stats,
            'config': {
                'character_similarity_threshold': self.config.character_similarity_threshold,
                'min_character_appearances': self.config.min_character_appearances
            }
        }
        
        for char_id, character in self.characters.items():
            data['characters'][str(char_id)] = {
                'character_id': character.character_id,
                'track_ids': character.track_ids,
                'first_appearance': character.first_appearance,
                'last_appearance': character.last_appearance,
                'total_frames': character.total_frames,
                'num_embeddings': len(character.embeddings),
                'appearances': [
                    {
                        'track_id': int(face.track_id),
                        'frame_number': int(face.frame_number),
                        'timestamp': float(face.timestamp),
                        'bbox': [int(x) for x in face.bbox],
                        'quality_score': float(face.quality_score)
                    }
                    for face in character.appearances[-10:]  # Save last 10 appearances
                ]
            }
        
        # Custom JSON encoder for numpy types
        import numpy as np
        
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, cls=NumpyEncoder)
        
        logger.info(f"Saved tracking data to {output_path}")