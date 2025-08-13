"""
Unified InsightFace Processor

This module provides a unified interface for face detection, alignment, and embedding
extraction using InsightFace's buffalo_l model, which includes RetinaFace detector
with facial landmarks for proper alignment.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path
import insightface
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)


@dataclass
class ProcessedFace:
    """Represents a fully processed face with all extracted information"""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    landmarks: np.ndarray  # 5 facial landmarks (eyes, nose, mouth corners)
    embedding: np.ndarray  # 512-dimensional face embedding
    aligned_face: np.ndarray  # Aligned face image (112x112)
    detection_score: float
    quality_score: float  # Overall quality score
    pose: Optional[Tuple[float, float, float]] = None  # yaw, pitch, roll
    age: Optional[int] = None
    gender: Optional[str] = None
    

@dataclass
class InsightFaceConfig:
    """Configuration for InsightFace processor"""
    model_name: str = 'buffalo_s'  # Using buffalo_s for compatibility
    device: str = 'cpu'  # 'cpu' or 'cuda'
    det_size: Tuple[int, int] = (640, 640)  # Detection input size
    det_thresh: float = 0.5  # Detection threshold
    min_face_size: int = 20  # Minimum face size in pixels
    enable_attributes: bool = True  # Extract age, gender, etc.
    

class InsightFaceProcessor:
    """Unified face processing using InsightFace buffalo_l model"""
    
    def __init__(self, config: InsightFaceConfig = None):
        """Initialize the processor
        
        Args:
            config: Configuration object
        """
        self.config = config or InsightFaceConfig()
        self.app = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize InsightFace FaceAnalysis app"""
        try:
            # buffalo_l includes: RetinaFace detector, landmark predictor, 
            # ArcFace recognition, and attribute prediction
            providers = ['CPUExecutionProvider']
            if self.config.device == 'cuda':
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                
            self.app = FaceAnalysis(
                name=self.config.model_name,
                providers=providers
            )
            
            # Prepare the app with detection settings
            ctx_id = 0 if self.config.device == 'cuda' else -1
            self.app.prepare(ctx_id=ctx_id, det_size=self.config.det_size)
            
            # Set detection threshold
            if hasattr(self.app, 'det_model'):
                self.app.det_model.det_thresh = self.config.det_thresh
            
            logger.info(f"Initialized InsightFace processor with {self.config.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace: {e}")
            raise
    
    def process_image(self, image: np.ndarray, 
                     return_aligned: bool = True) -> List[ProcessedFace]:
        """Process an image to extract all face information
        
        Args:
            image: Input image (BGR format)
            return_aligned: Whether to return aligned face images
            
        Returns:
            List of ProcessedFace objects
        """
        if self.app is None:
            raise RuntimeError("Model not initialized")
            
        # Detect and analyze faces
        faces = self.app.get(image)
        
        processed_faces = []
        for face in faces:
            # Extract bounding box
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # Check minimum face size
            face_width = x2 - x1
            face_height = y2 - y1
            if face_width < self.config.min_face_size or face_height < self.config.min_face_size:
                continue
            
            # Get detection score
            det_score = face.det_score
            
            # Extract landmarks (5-point for RetinaFace)
            landmarks = face.kps if hasattr(face, 'kps') else None
            
            # Get embedding
            embedding = face.embedding if hasattr(face, 'embedding') else None
            
            # Get aligned face if requested
            aligned_face = None
            if return_aligned and hasattr(face, 'normed_embedding'):
                # The face is already aligned internally by InsightFace
                # We can extract it from the detection
                aligned_face = self._extract_aligned_face(image, face)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(face, det_score)
            
            # Extract additional attributes if available
            pose = None
            age = None
            gender = None
            
            if self.config.enable_attributes:
                if hasattr(face, 'pose'):
                    pose = tuple(face.pose)
                if hasattr(face, 'age'):
                    age = int(face.age)
                if hasattr(face, 'gender'):
                    gender = 'M' if face.gender == 1 else 'F'
            
            processed_face = ProcessedFace(
                bbox=(x1, y1, x2, y2),
                landmarks=landmarks,
                embedding=embedding,
                aligned_face=aligned_face,
                detection_score=det_score,
                quality_score=quality_score,
                pose=pose,
                age=age,
                gender=gender
            )
            
            processed_faces.append(processed_face)
        
        # Sort by quality score (best first)
        processed_faces.sort(key=lambda f: f.quality_score, reverse=True)
        
        return processed_faces
    
    def _extract_aligned_face(self, image: np.ndarray, face: Any) -> np.ndarray:
        """Extract aligned face using landmarks
        
        Args:
            image: Original image
            face: Face object from InsightFace
            
        Returns:
            Aligned face image (112x112)
        """
        # InsightFace internally aligns faces for embedding extraction
        # We'll use their alignment transformation
        
        # Standard face template for alignment (112x112)
        src_pts = np.array([
            [38.2946, 51.6963],
            [73.5318, 51.5014],
            [56.0252, 71.7366],
            [41.5493, 92.3655],
            [70.7299, 92.2041]
        ], dtype=np.float32)
        
        if hasattr(face, 'kps') and face.kps is not None:
            # Get transformation matrix
            from skimage import transform as trans
            tform = trans.SimilarityTransform()
            tform.estimate(face.kps, src_pts)
            M = tform.params[0:2, :]
            
            # Apply transformation
            aligned = cv2.warpAffine(image, M, (112, 112), borderValue=0)
            return aligned
        
        # Fallback: crop and resize
        x1, y1, x2, y2 = face.bbox.astype(int)
        face_img = image[y1:y2, x1:x2]
        return cv2.resize(face_img, (112, 112))
    
    def _calculate_quality_score(self, face: Any, det_score: float) -> float:
        """Calculate overall face quality score
        
        Args:
            face: Face object from InsightFace
            det_score: Detection confidence score
            
        Returns:
            Quality score between 0 and 1
        """
        quality = det_score
        
        # Penalize extreme poses if available
        if hasattr(face, 'pose') and face.pose is not None:
            yaw, pitch, roll = face.pose
            # Penalize large angles (frontal face is best)
            pose_penalty = 1.0 - (abs(yaw) + abs(pitch) + abs(roll)) / 270.0
            quality *= pose_penalty
        
        # Penalize low-resolution faces
        if hasattr(face, 'bbox'):
            bbox = face.bbox
            face_size = min(bbox[2] - bbox[0], bbox[3] - bbox[1])
            size_score = min(face_size / 112.0, 1.0)  # Normalize to 112x112
            quality *= (0.5 + 0.5 * size_score)  # Don't penalize too much
        
        return quality
    
    def process_frame_region(self, frame: np.ndarray, 
                           region: Tuple[int, int, int, int],
                           expand_ratio: float = 0.2) -> Optional[ProcessedFace]:
        """Process a specific region of a frame (e.g., from YOLO detection)
        
        Args:
            frame: Full frame image
            region: Region of interest (x1, y1, x2, y2)
            expand_ratio: Ratio to expand the region for better detection
            
        Returns:
            Best face found in the region, or None
        """
        x1, y1, x2, y2 = region
        
        # Expand region
        width = x2 - x1
        height = y2 - y1
        expand_x = int(width * expand_ratio)
        expand_y = int(height * expand_ratio)
        
        # Apply expansion with bounds checking
        x1 = max(0, x1 - expand_x)
        y1 = max(0, y1 - expand_y)
        x2 = min(frame.shape[1], x2 + expand_x)
        y2 = min(frame.shape[0], y2 + expand_y)
        
        # Extract region
        region_img = frame[y1:y2, x1:x2]
        
        # Process the region
        faces = self.process_image(region_img)
        
        if faces:
            # Adjust coordinates to full frame
            best_face = faces[0]  # Already sorted by quality
            
            # Adjust bbox coordinates
            bbox = list(best_face.bbox)
            bbox[0] += x1
            bbox[1] += y1
            bbox[2] += x1
            bbox[3] += y1
            best_face.bbox = tuple(bbox)
            
            # Adjust landmarks if present
            if best_face.landmarks is not None:
                best_face.landmarks[:, 0] += x1
                best_face.landmarks[:, 1] += y1
            
            return best_face
        
        return None
    
    def batch_process_faces(self, face_images: List[np.ndarray]) -> List[Optional[ProcessedFace]]:
        """Process multiple face images efficiently
        
        Args:
            face_images: List of cropped face images
            
        Returns:
            List of ProcessedFace objects (None for failed extractions)
        """
        results = []
        
        for face_img in face_images:
            faces = self.process_image(face_img)
            results.append(faces[0] if faces else None)
        
        return results
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compare two face embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1 (1 = identical)
        """
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2)
        
        # Convert to 0-1 range
        return (similarity + 1) / 2