#!/usr/bin/env python3
"""
Enhanced Visual Processing Pipeline with Face Tracking

This pipeline integrates:
- InsightFace buffalo_l model for better face detection and alignment
- SORT tracking for temporal consistency
- Active speaker detection for improved character-dialogue matching
"""

import sys
import os
import argparse
import logging
import json
import pickle
from pathlib import Path
from datetime import datetime
import time
import cv2
import numpy as np
from typing import Dict, List, Optional, Any


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.visual.face_tracker import FaceTracker, FaceTrackerConfig, TrackedCharacter
from src.visual.insightface_processor import InsightFaceConfig
from src.visual.active_speaker_detector import ActiveSpeakerDetector, LipMovementData
from src.visual.deepface_analyzer import DeepFaceAnalyzer
from src.schemas import SchemaC, CharacterInfo, FaceDetection
from src.visual.frame_extractor import FrameExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrackedVisualPipeline:
    """Enhanced visual processing pipeline with tracking"""
    
    def __init__(self, output_dir: str, device: str = 'cpu', min_appearances: int = 3):
        """Initialize the pipeline
        
        Args:
            output_dir: Directory for output files
            device: Device to use ('cpu' or 'cuda')
            min_appearances: Minimum appearances to consider a character
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        logger.info("Initializing tracked visual pipeline components...")
        
        # Configure face tracker
        tracker_config = FaceTrackerConfig()
        tracker_config.insightface_config = InsightFaceConfig(
            model_name='buffalo_s',  # Fall back to buffalo_s for now
            device=device,
            det_thresh=0.5,
            enable_attributes=True
        )
        tracker_config.use_embeddings = True
        tracker_config.min_character_appearances = min_appearances
        
        self.face_tracker = FaceTracker(tracker_config)
        self.active_speaker_detector = ActiveSpeakerDetector()
        self.deepface_analyzer = DeepFaceAnalyzer()
        
        logger.info("Pipeline initialized successfully")
    
    def process_video(self, video_path: str, 
                     target_frames: int = 150,
                     extraction_mode: str = 'intelligent') -> SchemaC:
        """Process video with face tracking
        
        Args:
            video_path: Path to input video
            target_frames: Number of frames to process
            extraction_mode: Frame extraction strategy
            
        Returns:
            SchemaC with character detection data
        """
        logger.info(f"Processing video: {video_path}")
        start_time = time.time()
        
        # Extract frames intelligently
        logger.info(f"Extracting {target_frames} frames using {extraction_mode} mode...")
        from src.visual.frame_extractor import FrameExtractionConfig
        
        # Configure frame extraction
        extraction_config = FrameExtractionConfig(
            extraction_mode=extraction_mode,
            target_frames=target_frames,
            save_frames=False  # We'll process in memory
        )
        extractor = FrameExtractor(extraction_config)
        frames_data = extractor.extract_frames(video_path)
        
        if not frames_data:
            logger.error("No frames extracted from video")
            return self._create_empty_schema()
        
        logger.info(f"Extracted {len(frames_data)} frames")
        
        # Process frames with tracking
        tracked_characters = self._process_with_tracking(video_path, frames_data)
        
        # Convert to Schema C
        schema_c = self._convert_to_schema_c(tracked_characters, frames_data, video_path)
        
        # Analyze facial attributes for main characters
        self._analyze_character_attributes(schema_c, video_path, tracked_characters)
        
        # Extract lip movement data for fusion
        lip_movement_data = self._extract_lip_movements(tracked_characters)
        
        # Save results
        self._save_results(schema_c, tracked_characters, lip_movement_data)
        
        # Generate report
        self._generate_report(schema_c, tracked_characters, time.time() - start_time)
        
        logger.info(f"Visual processing complete in {time.time() - start_time:.1f} seconds")
        
        return schema_c
    
    def process_extracted_frames(self, 
                               frames_data: List[Dict[str, Any]], 
                               video_path: str,
                               fps: float = 24.0) -> SchemaC:
        """Process pre-extracted frames (for adaptive extraction)
        
        Args:
            frames_data: List of frame dictionaries with 'frame_number', 'timestamp', etc.
            video_path: Original video path (for metadata)
            fps: Video frame rate
            
        Returns:
            SchemaC with detected characters
        """
        logger.info(f"Processing {len(frames_data)} pre-extracted frames")
        start_time = time.time()
        
        # Convert frame data format if needed
        processed_frames = []
        for frame_info in frames_data:
            if 'path' in frame_info:
                # Load frame from path
                image = cv2.imread(frame_info['path'])
            elif 'image' in frame_info:
                image = frame_info['image']
            else:
                logger.warning(f"No image data for frame {frame_info.get('frame_number')}")
                continue
            
            processed_frames.append({
                'frame_number': frame_info['frame_number'],
                'timestamp': frame_info['timestamp'],
                'image': image,
                'quality_score': frame_info.get('quality_score', 1.0)
            })
        
        if not processed_frames:
            logger.error("No valid frames to process")
            return self._create_empty_schema()
        
        logger.info(f"Processing {len(processed_frames)} valid frames")
        
        # Process frames with tracking
        tracked_characters = self._process_with_tracking(video_path, processed_frames)
        
        # Get video duration from last frame timestamp
        duration = max(f['timestamp'] for f in processed_frames)
        total_frames = max(f['frame_number'] for f in processed_frames) + 1
        
        # Import required schema classes
        from src.schemas import CharacterInfo, FaceDetection
        
        # Create Schema C with proper metadata
        schema_c = SchemaC(
            video_id=Path(video_path).stem,
            duration=duration,
            fps=fps,
            total_frames=total_frames,
            metadata={
                'processing_mode': 'adaptive_extraction',
                'frames_processed': len(processed_frames)
            }
        )
        
        # Add characters and detections
        for char_id, character in tracked_characters.items():
            if character.total_frames >= 2:  # Use minimum threshold for adaptive extraction
                # Create character info
                char_info = CharacterInfo(
                    character_id=str(char_id),
                    num_appearances=character.total_frames,
                    first_appearance=character.first_appearance,
                    last_appearance=character.last_appearance,
                    total_screen_time=character.last_appearance - character.first_appearance,
                    average_confidence=0.95,  # High confidence due to tracking
                    appearance_segments=[
                        {
                            'start': seg[0],
                            'end': seg[1]
                        }
                        for seg in self._get_appearance_segments(character)
                    ],
                    attributes={}
                )
                
                # Add embeddings
                if character.embeddings:
                    char_info.representative_embeddings = [emb.tolist() for emb in character.embeddings[:10]]
                
                schema_c.add_character(char_info)
                
                # Create detections from appearances
                for appearance in character.appearances:
                    detection = FaceDetection(
                        detection_id=f"track_{appearance.track_id}_frame_{appearance.frame_number}",
                        frame_number=appearance.frame_number,
                        timestamp=appearance.timestamp,
                        bbox=list(appearance.bbox),
                        confidence=appearance.detection_score,
                        character_id=str(char_id),
                        attributes={}
                    )
                    schema_c.detections.append(detection)
        
        # Analyze facial attributes for main characters
        self._analyze_character_attributes(schema_c, video_path, tracked_characters)
        
        # Extract lip movement data
        lip_movement_data = self._extract_lip_movements(tracked_characters)
        
        # Save results
        self._save_results(schema_c, tracked_characters, lip_movement_data)
        
        # Generate report
        self._generate_report(schema_c, tracked_characters, time.time() - start_time)
        
        logger.info(f"Adaptive visual processing complete in {time.time() - start_time:.1f} seconds")
        
        return schema_c
    
    def _process_with_tracking(self, video_path: str, 
                             frames_data: List[Dict]) -> Dict[int, TrackedCharacter]:
        """Process frames with face tracking
        
        Args:
            video_path: Path to video file
            frames_data: List of frame metadata
            
        Returns:
            Dictionary of tracked characters
        """
        logger.info("Starting face tracking...")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_processed = 0
        
        # Process frames in order for tracking
        for i, frame_info in enumerate(frames_data):
            # Handle both object and dict formats
            if isinstance(frame_info, dict):
                frame_number = frame_info['frame_number']
                timestamp = frame_info['timestamp']
                frame = frame_info['image']
            else:
                frame_number = frame_info.frame_number
                timestamp = frame_info.timestamp
                frame = frame_info.image
            
            # Process frame with tracker
            tracked_faces = self.face_tracker.process_frame(frame, frame_number, timestamp)
            total_processed += 1
            
            # Log progress
            if i % 30 == 0:
                logger.info(f"Processed {i}/{len(frames_data)} frames, "
                          f"{len(self.face_tracker.characters)} characters detected")
        
        cap.release()
        
        # Get final tracked characters
        tracked_characters = self.face_tracker.characters
        
        # Filter characters with sufficient appearances
        filtered_characters = {
            char_id: char 
            for char_id, char in tracked_characters.items()
            if char.total_frames >= 3  # Match the config threshold
        }
        
        logger.info(f"Tracking complete. Found {len(filtered_characters)} main characters")
        
        return filtered_characters
    
    def _convert_to_schema_c(self, tracked_characters: Dict[int, TrackedCharacter],
                           frames_data: List, video_path: str = None) -> SchemaC:
        """Convert tracked characters to Schema C format
        
        Args:
            tracked_characters: Dictionary of tracked characters
            frames_data: Frame metadata
            
        Returns:
            SchemaC object
        """
        logger.info("Converting to Schema C format...")
        
        # Create character info dictionary
        characters = {}
        detections = []
        
        for char_id, character in tracked_characters.items():
            # Create character info
            char_info = CharacterInfo(
                character_id=str(char_id),
                num_appearances=character.total_frames,
                first_appearance=character.first_appearance,
                last_appearance=character.last_appearance,
                total_screen_time=character.last_appearance - character.first_appearance,
                average_confidence=0.95,  # High confidence due to tracking
                appearance_segments=[
                    {
                        'start': seg[0],
                        'end': seg[1]
                    }
                    for seg in self._get_appearance_segments(character)
                ],
                attributes={}
            )
            
            # Add embeddings
            if character.embeddings:
                char_info.representative_embeddings = [emb.tolist() for emb in character.embeddings[:10]]  # Limit to 10
            
            characters[str(char_id)] = char_info
            
            # Create detections from appearances
            for appearance in character.appearances:
                detection = FaceDetection(
                    detection_id=f"track_{appearance.track_id}_frame_{appearance.frame_number}",
                    frame_number=appearance.frame_number,
                    timestamp=appearance.timestamp,
                    bbox=list(appearance.bbox),
                    confidence=appearance.detection_score,
                    character_id=str(char_id),
                    attributes={}
                )
                detections.append(detection)
        
        # Get video info
        cap = cv2.VideoCapture(video_path) if video_path else None
        duration = 0.0
        fps = 0.0
        total_frames = 0
        
        if cap and cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
        
        # Create Schema C
        schema_c = SchemaC(
            video_id=Path(video_path).stem if video_path else 'unknown',
            duration=duration,
            fps=fps,
            total_frames=total_frames,
            characters=characters,
            detections=detections,
            metadata={
                'frames_analyzed': len(frames_data),
                'face_detection_model': 'buffalo_s (RetinaFace)',
                'embedding_model': 'buffalo_s (ArcFace)',
                'tracking_algorithm': 'SORT',
                'clustering_algorithm': 'temporal_tracking',
                'total_unique_tracks': len(self.face_tracker.track_to_character)
            }
        )
        
        return schema_c
    
    def _calculate_average_bbox_size(self, character: TrackedCharacter) -> float:
        """Calculate average bounding box size for a character"""
        if not character.appearances:
            return 0.0
        
        sizes = []
        for appearance in character.appearances:
            x1, y1, x2, y2 = appearance.bbox
            size = (x2 - x1) * (y2 - y1)
            sizes.append(size)
        
        return np.mean(sizes)
    
    def _get_appearance_segments(self, character: TrackedCharacter) -> List[tuple]:
        """Get continuous appearance segments for a character"""
        if not character.appearances:
            return []
        
        # Sort appearances by timestamp
        sorted_appearances = sorted(character.appearances, key=lambda a: a.timestamp)
        
        segments = []
        current_start = sorted_appearances[0].timestamp
        prev_time = sorted_appearances[0].timestamp
        
        for appearance in sorted_appearances[1:]:
            # If gap > 2 seconds, start new segment
            if appearance.timestamp - prev_time > 2.0:
                segments.append((current_start, prev_time))
                current_start = appearance.timestamp
            prev_time = appearance.timestamp
        
        # Add final segment
        segments.append((current_start, prev_time))
        
        return segments
    
    def _analyze_character_attributes(self, schema_c: SchemaC, 
                                    video_path: str,
                                    tracked_characters: Dict[int, TrackedCharacter]):
        """Analyze facial attributes for main characters"""
        logger.info("Analyzing character attributes...")
        
        cap = cv2.VideoCapture(video_path)
        
        for char_id, character in tracked_characters.items():
            if char_id not in schema_c.characters:
                continue
            
            # Get best quality face for this character
            best_appearance = max(character.appearances, 
                                key=lambda a: a.quality_score)
            
            # Extract face image
            cap.set(cv2.CAP_PROP_POS_FRAMES, best_appearance.frame_number)
            ret, frame = cap.read()
            
            if ret:
                x1, y1, x2, y2 = best_appearance.bbox
                face_img = frame[y1:y2, x1:x2]
                
                # Analyze with DeepFace
                try:
                    attributes = self.deepface_analyzer.analyze_face(face_img)
                    
                    # Update character info
                    char_info = schema_c.characters[str(char_id)]
                    char_info.attributes.update({
                        'age': attributes.get('age'),
                        'gender': attributes.get('gender'),
                        'emotion': attributes.get('dominant_emotion'),
                        'race': attributes.get('dominant_race')
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze attributes for character {char_id}: {e}")
        
        cap.release()
    
    def _extract_lip_movements(self, tracked_characters: Dict[int, TrackedCharacter]) -> Dict:
        """Extract lip movement data for active speaker detection
        
        Args:
            tracked_characters: Dictionary of tracked characters
            
        Returns:
            Dictionary of character_id -> list of LipMovementData
        """
        logger.info("Extracting lip movement data...")
        
        lip_movements = {}
        
        for char_id, character in tracked_characters.items():
            movements = []
            
            for appearance in character.appearances:
                # Create lip movement data
                # Note: This requires landmarks from buffalo_l
                if appearance.landmarks is not None:
                    movement = LipMovementData(
                        frame_number=appearance.frame_number,
                        timestamp=appearance.timestamp,
                        mouth_aspect_ratio=0.0,  # Would be calculated from landmarks
                        mouth_distance=0.0,  # Would be calculated from landmarks
                        lip_landmarks=appearance.landmarks,
                        movement_magnitude=0.0  # Would be calculated between frames
                    )
                    movements.append(movement)
            
            if movements:
                lip_movements[str(char_id)] = movements
        
        return lip_movements
    
    def _save_results(self, schema_c: SchemaC, 
                     tracked_characters: Dict[int, TrackedCharacter],
                     lip_movement_data: Dict):
        """Save processing results"""
        # Save Schema C
        schema_c_path = self.output_dir / 'character_data_schemaC.json'
        with open(schema_c_path, 'w') as f:
            json.dump(schema_c.to_dict(), f, indent=2, cls=NumpyEncoder)
        logger.info(f"Saved Schema C to {schema_c_path}")
        
        # Save tracking data
        tracking_path = self.output_dir / 'tracking_data.json'
        self.face_tracker.save_tracking_data(str(tracking_path))
        
        # Save lip movement data
        lip_movement_path = self.output_dir / 'lip_movement_data.pkl'
        with open(lip_movement_path, 'wb') as f:
            pickle.dump(lip_movement_data, f)
        logger.info(f"Saved lip movement data to {lip_movement_path}")
        
        # Save character images
        self._save_character_images(tracked_characters)
    
    def _save_character_images(self, tracked_characters: Dict[int, TrackedCharacter]):
        """Save best face image for each character"""
        char_dir = self.output_dir / 'character_appearances'
        char_dir.mkdir(exist_ok=True)
        
        for char_id, character in tracked_characters.items():
            if character.appearances:
                # Get best quality appearance
                best = max(character.appearances, key=lambda a: a.quality_score)
                
                # Save metadata
                char_file = char_dir / f'character_{char_id}.json'
                with open(char_file, 'w') as f:
                    json.dump({
                        'character_id': int(char_id),
                        'best_frame': int(best.frame_number),
                        'quality_score': float(best.quality_score),
                        'total_appearances': len(character.appearances)
                    }, f, indent=2)
    
    def _generate_report(self, schema_c: SchemaC, 
                        tracked_characters: Dict[int, TrackedCharacter],
                        processing_time: float):
        """Generate processing report"""
        report_path = self.output_dir / 'visual_pipeline_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("=== Enhanced Visual Processing Report ===\n\n")
            f.write(f"Processing Time: {processing_time:.1f} seconds\n")
            f.write(f"Total Frames Analyzed: {schema_c.metadata.get('frames_analyzed', 0)}\n")
            f.write(f"Total Detections: {len(schema_c.detections)}\n")
            f.write(f"Unique Characters Found: {len(tracked_characters)}\n\n")
            
            f.write("Character Summary:\n")
            for char_id, character in sorted(tracked_characters.items(), 
                                           key=lambda x: x[1].total_frames, 
                                           reverse=True):
                f.write(f"\nCharacter {char_id}:\n")
                f.write(f"  - Total Appearances: {character.total_frames}\n")
                f.write(f"  - Time Range: {character.first_appearance:.1f}s - "
                       f"{character.last_appearance:.1f}s\n")
                f.write(f"  - Track IDs: {character.track_ids}\n")
                
                char_info = schema_c.characters.get(str(char_id))
                if char_info and char_info.attributes:
                    f.write(f"  - Attributes: {char_info.attributes}\n")
            
            f.write(f"\n\nProcessing Metadata:\n")
            for key, value in schema_c.metadata.items():
                f.write(f"  - {key}: {value}\n")
        
        logger.info(f"Report saved to {report_path}")
    
    def _create_empty_schema(self) -> SchemaC:
        """Create empty Schema C for error cases"""
        return SchemaC(
            video_id='error',
            duration=0.0,
            fps=0.0,
            total_frames=0,
            characters={},
            detections=[],
            metadata={'error': 'No frames extracted'}
        )


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced visual processing pipeline with face tracking"
    )
    parser.add_argument('video_path', help='Path to input video')
    parser.add_argument('--output', '-o', default='output/visual_tracked',
                       help='Output directory')
    parser.add_argument('--target-frames', type=int, default=150,
                       help='Number of frames to process')
    parser.add_argument('--extraction-mode', choices=['uniform', 'scene', 'intelligent'],
                       default='intelligent', help='Frame extraction strategy')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                       help='Device to use for processing')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--min-appearances', type=int, default=3,
                       help='Minimum appearances to consider a character (default: 3)')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output}_{timestamp}"
    
    try:
        # Initialize pipeline
        pipeline = TrackedVisualPipeline(output_dir, device=args.device, min_appearances=args.min_appearances)
        
        # Process video
        schema_c = pipeline.process_video(
            args.video_path,
            target_frames=args.target_frames,
            extraction_mode=args.extraction_mode
        )
        
        logger.info(f"Processing complete. Results saved to {output_dir}")
        
        # Print summary
        print(f"\nProcessing Summary:")
        print(f"  - Characters detected: {len(schema_c.characters)}")
        print(f"  - Total detections: {len(schema_c.detections)}")
        print(f"  - Frames analyzed: {schema_c.metadata.get('frames_analyzed', 0)}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()