"""
Wav2Vec2 Emotion Recognition Processor
Adds emotion labels to Schema A segments
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
from dataclasses import dataclass
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import librosa
import soundfile as sf

from ..schemas import SchemaA, TranscriptionSegment


@dataclass
class EmotionConfig:
    """Configuration for Emotion processor"""
    model_name: str = "superb/wav2vec2-large-superb-er"
    device: Optional[str] = None  # None for auto-detect
    sampling_rate: int = 16000  # wav2vec2 expects 16kHz
    chunk_length_s: float = 10.0  # Process in 10-second chunks for memory efficiency
    stride_length_s: float = 1.0  # Overlap between chunks
    batch_size: int = 8  # Number of chunks to process at once
    aggregation_strategy: str = "mean"  # How to aggregate chunk predictions: mean, max, or weighted
    confidence_threshold: float = 0.5  # Minimum confidence to assign emotion


class EmotionProcessor:
    """Wav2Vec2 emotion processor for audio emotion recognition"""
    
    # Emotion labels from SUPERB model
    EMOTION_LABELS = ['angry', 'happy', 'sad', 'surprise', 'fear', 'disgust', 'neutral']
    
    def __init__(self, config: Optional[EmotionConfig] = None):
        """Initialize Emotion processor
        
        Args:
            config: EmotionConfig object or None for defaults
        """
        self.config = config or EmotionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Set device
        if self.config.device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(self.config.device)
        
        # Load model and feature extractor
        self.logger.info(f"Loading wav2vec2 emotion model: {self.config.model_name}")
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(self.config.model_name)
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.config.model_name)
        
        # Move model to device
        self.model.to(self.device)
        self.model.eval()
        
        self.logger.info(f"Model loaded on device: {self.device}")
    
    def extract_audio_segment(self, audio_path: str, start_time: float, end_time: float) -> np.ndarray:
        """Extract audio segment from file
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Audio array at 16kHz
        """
        try:
            duration = end_time - start_time
            
            # Skip segments with zero or negative duration
            if duration <= 0:
                self.logger.debug(f"Skipping segment with zero/negative duration: {start_time}-{end_time}")
                return np.array([])
            
            # Ensure minimum duration for wav2vec2 (at least 0.025 seconds = 400 samples at 16kHz)
            min_duration = 0.025
            if duration < min_duration:
                self.logger.debug(f"Segment too short ({duration}s), padding to {min_duration}s")
                # Load with padding
                audio, sr = librosa.load(
                    audio_path, 
                    sr=self.config.sampling_rate,
                    offset=max(0, start_time - (min_duration - duration) / 2),
                    duration=min_duration
                )
            else:
                # Load normally
                audio, sr = librosa.load(
                    audio_path, 
                    sr=self.config.sampling_rate,
                    offset=start_time,
                    duration=duration
                )
            
            # Ensure minimum length (400 samples for wav2vec2)
            min_samples = 400
            if len(audio) < min_samples:
                # Pad with zeros
                pad_width = min_samples - len(audio)
                audio = np.pad(audio, (0, pad_width), mode='constant', constant_values=0)
                self.logger.debug(f"Padded audio from {len(audio) - pad_width} to {len(audio)} samples")
            
            return audio
        except Exception as e:
            self.logger.error(f"Error extracting audio segment: {e}")
            return np.array([])
    
    def predict_emotion(self, audio_array: np.ndarray) -> Tuple[str, float]:
        """Predict emotion from audio array
        
        Args:
            audio_array: Audio array at 16kHz
            
        Returns:
            Tuple of (emotion_label, confidence_score)
        """
        if len(audio_array) == 0:
            return "neutral", 0.0
        
        # Process in chunks if audio is long
        chunk_length = int(self.config.chunk_length_s * self.config.sampling_rate)
        stride_length = int(self.config.stride_length_s * self.config.sampling_rate)
        
        if len(audio_array) <= chunk_length:
            # Process entire audio at once
            chunks = [audio_array]
        else:
            # Split into overlapping chunks
            chunks = []
            for i in range(0, len(audio_array) - chunk_length + 1, stride_length):
                chunks.append(audio_array[i:i + chunk_length])
            
            # Add final chunk if there's remaining audio
            if len(audio_array) % stride_length != 0:
                chunks.append(audio_array[-chunk_length:])
        
        # Process chunks in batches
        all_predictions = []
        all_confidences = []
        
        for i in range(0, len(chunks), self.config.batch_size):
            batch_chunks = chunks[i:i + self.config.batch_size]
            
            # Prepare inputs
            inputs = self.feature_extractor(
                batch_chunks,
                sampling_rate=self.config.sampling_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                
                # Get probabilities
                probs = torch.nn.functional.softmax(logits, dim=-1)
                
                # Get predictions and confidences for each chunk
                for j in range(len(batch_chunks)):
                    chunk_probs = probs[j].cpu().numpy()
                    pred_idx = np.argmax(chunk_probs)
                    confidence = chunk_probs[pred_idx]
                    
                    all_predictions.append(pred_idx)
                    all_confidences.append(confidence)
        
        # Aggregate predictions
        if self.config.aggregation_strategy == "mean":
            # Average probabilities across chunks
            avg_probs = np.zeros(len(self.EMOTION_LABELS))
            for pred_idx, conf in zip(all_predictions, all_confidences):
                avg_probs[pred_idx] += conf
            avg_probs /= len(all_predictions)
            
            final_pred_idx = np.argmax(avg_probs)
            final_confidence = avg_probs[final_pred_idx]
            
        elif self.config.aggregation_strategy == "max":
            # Use prediction with highest confidence
            max_conf_idx = np.argmax(all_confidences)
            final_pred_idx = all_predictions[max_conf_idx]
            final_confidence = all_confidences[max_conf_idx]
            
        else:  # weighted
            # Weight by confidence scores
            weighted_probs = np.zeros(len(self.EMOTION_LABELS))
            total_weight = sum(all_confidences)
            
            for pred_idx, conf in zip(all_predictions, all_confidences):
                weighted_probs[pred_idx] += conf * conf / total_weight
                
            final_pred_idx = np.argmax(weighted_probs)
            final_confidence = weighted_probs[final_pred_idx]
        
        emotion = self.EMOTION_LABELS[final_pred_idx]
        
        # Apply confidence threshold
        if final_confidence < self.config.confidence_threshold:
            emotion = "neutral"
            final_confidence = 1.0 - final_confidence  # Confidence in neutral
        
        return emotion, float(final_confidence)
    
    def process_segments(self, audio_path: str, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        """Process emotion for each segment
        
        Args:
            audio_path: Path to audio file
            segments: List of transcription segments
            
        Returns:
            Updated segments with emotion labels
        """
        self.logger.info(f"Processing emotions for {len(segments)} segments")
        
        for i, segment in enumerate(segments):
            if segment.source == "whisper":  # Only process speech segments
                # Skip empty text segments
                if not segment.text or segment.text.strip() == "":
                    segment.emotion = "neutral"
                    segment.emotion_confidence = 0.0
                    self.logger.debug(f"Segment {i}: Empty text, skipping emotion processing")
                    continue
                
                # Extract audio for this segment
                audio_segment = self.extract_audio_segment(
                    audio_path,
                    segment.start_time,
                    segment.end_time
                )
                
                # Skip if no audio extracted
                if len(audio_segment) == 0:
                    segment.emotion = "neutral"
                    segment.emotion_confidence = 0.0
                    self.logger.debug(f"Segment {i}: No audio extracted, skipping emotion processing")
                    continue
                
                # Predict emotion
                emotion, confidence = self.predict_emotion(audio_segment)
                
                # Update segment
                segment.emotion = emotion
                segment.emotion_confidence = confidence
                
                self.logger.debug(
                    f"Segment {i}: {segment.text[:50]}... -> "
                    f"{emotion} ({confidence:.2f})"
                )
        
        return segments
    
    def enhance_schema_a(self, schema_a: SchemaA, audio_path: str) -> SchemaA:
        """Enhance existing Schema A with emotion labels
        
        Args:
            schema_a: Existing Schema A object
            audio_path: Path to audio file
            
        Returns:
            Enhanced Schema A with emotion labels
        """
        self.logger.info(f"Enhancing Schema A for video: {schema_a.video_id}")
        
        # Process segments
        enhanced_segments = self.process_segments(audio_path, schema_a.segments)
        
        # Update schema
        schema_a.segments = enhanced_segments
        
        # Log summary
        emotion_counts = {}
        for segment in enhanced_segments:
            if segment.emotion:
                emotion_counts[segment.emotion] = emotion_counts.get(segment.emotion, 0) + 1
        
        self.logger.info(f"Emotion distribution: {emotion_counts}")
        
        return schema_a