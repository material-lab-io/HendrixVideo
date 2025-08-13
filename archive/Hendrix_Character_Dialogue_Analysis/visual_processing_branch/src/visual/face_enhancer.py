"""
Face Enhancement Module

This module provides face enhancement capabilities to improve
low-quality face images before embedding extraction.
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FaceEnhancer:
    """Enhances face images for better embedding extraction"""
    
    def __init__(self):
        """Initialize face enhancer"""
        self.target_size = (112, 112)  # Standard size for face recognition
        
    def enhance_face(self, face_image: np.ndarray, 
                    enhance_contrast: bool = True,
                    denoise: bool = True,
                    sharpen: bool = True) -> np.ndarray:
        """Enhance a face image using multiple techniques
        
        Args:
            face_image: Input face image
            enhance_contrast: Apply contrast enhancement
            denoise: Apply denoising
            sharpen: Apply sharpening
            
        Returns:
            Enhanced face image
        """
        enhanced = face_image.copy()
        
        # 1. Resize to minimum acceptable size if too small
        h, w = enhanced.shape[:2]
        if h < 64 or w < 64:
            scale = max(64/h, 64/w)
            new_h, new_w = int(h * scale), int(w * scale)
            enhanced = cv2.resize(enhanced, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logger.debug(f"Upscaled face from {w}x{h} to {new_w}x{new_h}")
        
        # 2. Denoise
        if denoise and enhanced.shape[0] >= 5 and enhanced.shape[1] >= 5:
            enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        # 3. Enhance contrast using CLAHE
        if enhance_contrast:
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 4. Sharpen
        if sharpen:
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]]) / 1.0
            enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 5. Adjust brightness if needed
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        if brightness < 60:  # Too dark
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.5, beta=30)
        elif brightness > 200:  # Too bright
            enhanced = cv2.convertScaleAbs(enhanced, alpha=0.8, beta=-20)
        
        return enhanced
    
    def align_face(self, face_image: np.ndarray, 
                  landmarks: Optional[np.ndarray] = None) -> np.ndarray:
        """Align face using facial landmarks or center crop
        
        Args:
            face_image: Input face image
            landmarks: Optional facial landmarks
            
        Returns:
            Aligned face image
        """
        h, w = face_image.shape[:2]
        
        if landmarks is not None and len(landmarks) >= 5:
            # Use landmarks for alignment (if available)
            # This would require more complex transformation
            pass
        else:
            # Simple center crop with padding
            if h > w:
                pad = (h - w) // 2
                face_image = cv2.copyMakeBorder(face_image, 0, 0, pad, pad, 
                                              cv2.BORDER_REFLECT)
            elif w > h:
                pad = (w - h) // 2
                face_image = cv2.copyMakeBorder(face_image, pad, pad, 0, 0, 
                                              cv2.BORDER_REFLECT)
        
        # Resize to target size
        face_image = cv2.resize(face_image, self.target_size, 
                               interpolation=cv2.INTER_LINEAR)
        
        return face_image
    
    def preprocess_for_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """Complete preprocessing pipeline for embedding extraction
        
        Args:
            face_image: Input face image
            
        Returns:
            Preprocessed face ready for embedding
        """
        # Enhance face
        enhanced = self.enhance_face(face_image)
        
        # Align and resize
        aligned = self.align_face(enhanced)
        
        return aligned
    
    def assess_face_quality(self, face_image: np.ndarray) -> dict:
        """Assess face image quality
        
        Returns:
            Dictionary with quality metrics
        """
        h, w = face_image.shape[:2]
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Calculate metrics
        metrics = {
            'size': (w, h),
            'resolution_score': min(w, h) / 112.0,  # Normalized to target size
            'blur_score': cv2.Laplacian(gray, cv2.CV_64F).var(),
            'brightness': np.mean(gray),
            'contrast': np.std(gray)
        }
        
        # Overall quality score
        size_score = min(1.0, min(w, h) / 30.0)
        blur_score = min(1.0, metrics['blur_score'] / 100.0)
        brightness_score = 1.0 - abs(metrics['brightness'] - 128) / 128.0
        contrast_score = min(1.0, metrics['contrast'] / 50.0)
        
        metrics['overall_quality'] = (
            size_score * 0.3 + 
            blur_score * 0.3 + 
            brightness_score * 0.2 + 
            contrast_score * 0.2
        )
        
        return metrics