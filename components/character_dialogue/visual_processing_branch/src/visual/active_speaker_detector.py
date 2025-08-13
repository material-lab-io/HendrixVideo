"""
Active Speaker Detection Module

Detects which character is speaking by analyzing facial landmarks,
particularly lip movements, and correlating with audio.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
from scipy.signal import find_peaks
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class LipMovementData:
    """Data for lip movement analysis"""
    frame_number: int
    timestamp: float
    mouth_aspect_ratio: float  # MAR - measure of mouth openness
    mouth_distance: float  # Distance between upper and lower lip
    lip_landmarks: np.ndarray  # Lip landmark positions
    movement_magnitude: float  # Change from previous frame
    

@dataclass
class SpeakerDetectionResult:
    """Result of active speaker detection"""
    character_id: int
    confidence: float
    start_time: float
    end_time: float
    lip_sync_score: float
    audio_correlation: float
    

class ActiveSpeakerDetector:
    """Detects active speakers by analyzing lip movements"""
    
    def __init__(self, window_size: int = 15, movement_threshold: float = 0.15):
        """Initialize active speaker detector
        
        Args:
            window_size: Number of frames to analyze for movement patterns
            movement_threshold: Minimum movement to consider as speaking
        """
        self.window_size = window_size
        self.movement_threshold = movement_threshold
        
        # Buffers for temporal analysis
        self.movement_history: Dict[int, deque] = {}  # character_id -> movement history
        self.landmark_history: Dict[int, deque] = {}  # character_id -> landmark history
        
        # Lip landmark indices for different face models
        # For 68-point model
        self.lip_indices_68 = {
            'outer_upper': list(range(48, 55)),  # 48-54
            'outer_lower': list(range(54, 60)) + [48],  # 54-59, 48
            'inner_upper': list(range(60, 65)),  # 60-64
            'inner_lower': list(range(64, 68)) + [60],  # 64-67, 60
        }
        
        # For 5-point model (simplified)
        self.lip_indices_5 = {
            'left_corner': 3,
            'right_corner': 4,
        }
    
    def analyze_lip_movement(self, landmarks: np.ndarray, 
                           landmark_type: str = '68') -> Tuple[float, float]:
        """Analyze lip movement from facial landmarks
        
        Args:
            landmarks: Facial landmark positions
            landmark_type: Type of landmark model ('68', '106', '5')
            
        Returns:
            Tuple of (mouth_aspect_ratio, mouth_distance)
        """
        if landmark_type == '68' and len(landmarks) >= 68:
            return self._analyze_68_point_lips(landmarks)
        elif landmark_type == '5' and len(landmarks) >= 5:
            return self._analyze_5_point_lips(landmarks)
        else:
            # Fallback: estimate from bounding box or available points
            return 0.0, 0.0
    
    def _analyze_68_point_lips(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """Analyze lips using 68-point landmark model"""
        # Get lip landmarks
        upper_lip = landmarks[self.lip_indices_68['outer_upper']]
        lower_lip = landmarks[self.lip_indices_68['outer_lower']]
        
        # Calculate vertical mouth opening (MAR - Mouth Aspect Ratio)
        # Similar to EAR (Eye Aspect Ratio) for blink detection
        vertical_distances = []
        
        # Calculate distances between corresponding upper and lower lip points
        for i in range(3):  # Use middle 3 pairs for stability
            upper_idx = 50 + i  # Points 50, 51, 52
            lower_idx = 58 - i  # Points 58, 57, 56
            
            if upper_idx < len(landmarks) and lower_idx < len(landmarks):
                dist = np.linalg.norm(landmarks[upper_idx] - landmarks[lower_idx])
                vertical_distances.append(dist)
        
        # Horizontal mouth distance (corner to corner)
        left_corner = landmarks[48]
        right_corner = landmarks[54]
        horizontal_distance = np.linalg.norm(right_corner - left_corner)
        
        # Calculate MAR
        if vertical_distances and horizontal_distance > 0:
            mar = np.mean(vertical_distances) / horizontal_distance
        else:
            mar = 0.0
        
        # Average vertical distance (mouth openness)
        mouth_distance = np.mean(vertical_distances) if vertical_distances else 0.0
        
        return mar, mouth_distance
    
    def _analyze_5_point_lips(self, landmarks: np.ndarray) -> Tuple[float, float]:
        """Analyze lips using 5-point landmark model (simplified)"""
        # With only 5 points, we can only estimate based on mouth corners
        left_corner = landmarks[self.lip_indices_5['left_corner']]
        right_corner = landmarks[self.lip_indices_5['right_corner']]
        
        # Estimate mouth width
        mouth_width = np.linalg.norm(right_corner - left_corner)
        
        # Very rough estimation - assume mouth height is proportional to width when speaking
        estimated_mar = 0.15  # Default neutral position
        
        return estimated_mar, mouth_width * 0.3
    
    def update_character_frame(self, character_id: int, 
                             landmarks: np.ndarray,
                             frame_number: int,
                             timestamp: float,
                             landmark_type: str = '68') -> LipMovementData:
        """Update lip movement data for a character in a frame
        
        Args:
            character_id: ID of the character
            landmarks: Facial landmarks
            frame_number: Current frame number
            timestamp: Frame timestamp
            landmark_type: Type of landmark model
            
        Returns:
            LipMovementData for this frame
        """
        # Initialize history if needed
        if character_id not in self.movement_history:
            self.movement_history[character_id] = deque(maxlen=self.window_size)
            self.landmark_history[character_id] = deque(maxlen=self.window_size)
        
        # Analyze current lip position
        mar, mouth_distance = self.analyze_lip_movement(landmarks, landmark_type)
        
        # Calculate movement magnitude from previous frame
        movement_magnitude = 0.0
        if self.landmark_history[character_id]:
            prev_landmarks = self.landmark_history[character_id][-1]
            
            # Calculate landmark displacement
            if prev_landmarks.shape == landmarks.shape:
                displacement = np.mean(np.linalg.norm(landmarks - prev_landmarks, axis=1))
                movement_magnitude = displacement
        
        # Create movement data
        movement_data = LipMovementData(
            frame_number=frame_number,
            timestamp=timestamp,
            mouth_aspect_ratio=mar,
            mouth_distance=mouth_distance,
            lip_landmarks=landmarks.copy(),
            movement_magnitude=movement_magnitude
        )
        
        # Update history
        self.movement_history[character_id].append(movement_data)
        self.landmark_history[character_id].append(landmarks)
        
        return movement_data
    
    def detect_speaking(self, character_id: int, 
                       audio_amplitude: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """Detect if a character is speaking based on lip movement history
        
        Args:
            character_id: ID of the character to analyze
            audio_amplitude: Optional audio amplitude data for correlation
            
        Returns:
            Tuple of (is_speaking, confidence_score)
        """
        if character_id not in self.movement_history:
            return False, 0.0
        
        history = list(self.movement_history[character_id])
        
        if len(history) < 3:  # Need at least 3 frames
            return False, 0.0
        
        # Extract movement features
        mars = [h.mouth_aspect_ratio for h in history]
        movements = [h.movement_magnitude for h in history]
        
        # Calculate statistics
        mar_mean = np.mean(mars)
        mar_std = np.std(mars)
        movement_mean = np.mean(movements)
        
        # Speaking indicators
        speaking_score = 0.0
        
        # 1. Mouth aspect ratio variation (mouth opening/closing)
        if mar_std > 0.02:  # Significant variation
            speaking_score += 0.3
        
        # 2. Average mouth openness
        if mar_mean > 0.15:  # Mouth is open
            speaking_score += 0.2
        
        # 3. Consistent movement
        if movement_mean > self.movement_threshold:
            speaking_score += 0.3
        
        # 4. Movement pattern analysis (periodic movement)
        if self._detect_speech_pattern(mars):
            speaking_score += 0.2
        
        # 5. Audio correlation if available
        if audio_amplitude is not None:
            correlation = self._correlate_with_audio(history, audio_amplitude)
            speaking_score = 0.7 * speaking_score + 0.3 * correlation
        
        # Determine if speaking
        is_speaking = speaking_score > 0.5
        
        return is_speaking, min(speaking_score, 1.0)
    
    def _detect_speech_pattern(self, mars: List[float]) -> bool:
        """Detect speech-like patterns in mouth aspect ratios"""
        if len(mars) < 5:
            return False
        
        # Convert to numpy array
        mar_array = np.array(mars)
        
        # Look for periodic opening/closing
        # Speech typically has 3-8 Hz mouth movement
        # With 30 FPS video, that's peaks every 4-10 frames
        
        # Find peaks (mouth opening moments)
        peaks, properties = find_peaks(mar_array, 
                                     height=np.mean(mar_array) + 0.5 * np.std(mar_array),
                                     distance=2)
        
        # Check if we have regular peaks
        if len(peaks) >= 2:
            # Check if peaks are somewhat regular
            peak_distances = np.diff(peaks)
            if len(peak_distances) > 0:
                distance_std = np.std(peak_distances)
                distance_mean = np.mean(peak_distances)
                
                # Regular pattern if std is small relative to mean
                if distance_mean > 0 and distance_std / distance_mean < 0.5:
                    return True
        
        return False
    
    def _correlate_with_audio(self, movement_history: List[LipMovementData], 
                            audio_amplitude: np.ndarray) -> float:
        """Correlate lip movement with audio amplitude
        
        Args:
            movement_history: List of lip movement data
            audio_amplitude: Audio amplitude values
            
        Returns:
            Correlation score between 0 and 1
        """
        if len(movement_history) < 3 or len(audio_amplitude) < 3:
            return 0.0
        
        # Extract movement magnitudes
        movements = np.array([h.movement_magnitude for h in movement_history])
        
        # Normalize both signals
        if np.std(movements) > 0:
            movements = (movements - np.mean(movements)) / np.std(movements)
        else:
            return 0.0
            
        if np.std(audio_amplitude) > 0:
            audio_norm = (audio_amplitude - np.mean(audio_amplitude)) / np.std(audio_amplitude)
        else:
            return 0.0
        
        # Ensure same length
        min_len = min(len(movements), len(audio_norm))
        movements = movements[:min_len]
        audio_norm = audio_norm[:min_len]
        
        # Calculate correlation
        correlation = np.corrcoef(movements, audio_norm)[0, 1]
        
        # Convert to 0-1 range
        return (correlation + 1) / 2 if not np.isnan(correlation) else 0.0
    
    def find_active_speaker(self, character_movements: Dict[int, LipMovementData],
                          audio_data: Optional[Dict] = None) -> Optional[SpeakerDetectionResult]:
        """Find the most likely active speaker among multiple characters
        
        Args:
            character_movements: Dict of character_id -> current LipMovementData
            audio_data: Optional audio information (amplitude, speaking segments)
            
        Returns:
            SpeakerDetectionResult for the most likely speaker, or None
        """
        best_score = 0.0
        best_character = None
        
        for char_id, movement in character_movements.items():
            # Update movement data
            self.update_character_frame(
                char_id, 
                movement.lip_landmarks,
                movement.frame_number,
                movement.timestamp
            )
            
            # Check if speaking
            is_speaking, confidence = self.detect_speaking(
                char_id,
                audio_data.get('amplitude') if audio_data else None
            )
            
            if is_speaking and confidence > best_score:
                best_score = confidence
                best_character = char_id
        
        if best_character is not None:
            # Get time range from movement history
            history = list(self.movement_history[best_character])
            start_time = history[0].timestamp
            end_time = history[-1].timestamp
            
            return SpeakerDetectionResult(
                character_id=best_character,
                confidence=best_score,
                start_time=start_time,
                end_time=end_time,
                lip_sync_score=best_score,
                audio_correlation=0.0  # Would be set if audio correlation was computed
            )
        
        return None
    
    def reset_character(self, character_id: int):
        """Reset movement history for a character"""
        if character_id in self.movement_history:
            self.movement_history[character_id].clear()
        if character_id in self.landmark_history:
            self.landmark_history[character_id].clear()