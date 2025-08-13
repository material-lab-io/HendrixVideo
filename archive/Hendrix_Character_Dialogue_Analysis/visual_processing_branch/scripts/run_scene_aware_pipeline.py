#!/usr/bin/env python3
"""
Scene-Aware Character Clustering Pipeline

Implements scene detection and scene-aware character clustering to better handle
costume changes and improve character consistency across scenes.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add audio branch to path
audio_branch = project_root.parent / 'audio_processing_branch'
sys.path.insert(0, str(audio_branch))

from src.visual.scene_detector import SceneDetector
from src.visual.scene_aware_character_clustering import SceneAwareCharacterClusterer
from src.visual.face_tracker import FaceTracker, FaceTrackerConfig
from src.visual.robust_frame_extractor import RobustFrameExtractor
from src.audio.audio_extractor import AudioExtractor
from src.audio.whisper_processor import WhisperProcessor, WhisperConfig
from src.audio.emotion_processor import EmotionProcessor
from src.audio.speaker_diarizer import SpeakerDiarizer
from src.fusion.advanced_character_matcher import AdvancedCharacterMatcher
from src.schemas import SchemaA, SchemaB, SchemaC, SchemaD, CharacterInfo, FaceDetection
from src.utils.config_loader import ConfigLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_output_directories(base_output_dir: str) -> Dict[str, Path]:
    """Create timestamped output directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path(base_output_dir) / f"scene_aware_session_{timestamp}"
    
    dirs = {
        'session': session_dir,
        'audio': session_dir / 'audio_output',
        'visual': session_dir / 'visual_output',
        'fusion': session_dir / 'fusion_output',
        'scenes': session_dir / 'scene_data'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        
    return dirs


def process_scenes(video_path: str, output_dirs: Dict[str, Path], 
                  scene_threshold: float = 30.0) -> SceneDetector:
    """Detect and save scene boundaries"""
    logger.info("Starting scene detection...")
    
    scene_detector = SceneDetector(
        threshold=scene_threshold,
        min_scene_len=15,
        use_adaptive=False
    )
    
    scenes = scene_detector.detect_scenes(video_path)
    
    # Save scene data
    scene_output = output_dirs['scenes'] / 'detected_scenes.json'
    scene_detector.save_scenes(str(scene_output))
    
    logger.info(f"Detected {len(scenes)} scenes")
    return scene_detector


def process_visual_with_scenes(video_path: str, output_dirs: Dict[str, Path],
                              scene_detector: SceneDetector,
                              target_frames: int = 600) -> SchemaC:
    """Process visual data with scene-aware tracking"""
    logger.info("Starting scene-aware visual processing...")
    
    # Configure face tracker with scene detection
    tracker_config = FaceTrackerConfig(
        character_similarity_threshold=0.7,
        min_character_appearances=5
    )
    
    face_tracker = FaceTracker(
        config=tracker_config,
        scene_detector=scene_detector
    )
    
    # Extract frames
    extractor = RobustFrameExtractor()
    frames, extraction_stats = extractor.extract_frames(
        video_path,
        target_frames=target_frames,
        extraction_mode='adaptive'
    )
    
    logger.info(f"Extracted {len(frames)} frames")
    
    # Process frames with scene-aware tracking
    for frame_data in frames:
        frame = frame_data['frame']
        frame_num = frame_data['frame_number']
        timestamp = frame_data['timestamp']
        
        face_tracker.process_frame(frame, frame_num, timestamp)
    
    # Get tracked characters
    characters = face_tracker.save_tracking_data(
        str(output_dirs['visual'] / 'tracking_data_with_scenes.json')
    )
    
    # Convert to Schema C with scene information
    schema_c = create_schema_c_with_scenes(
        video_path, characters, face_tracker, scene_detector
    )
    
    # Save Schema C
    schema_c.save_json(str(output_dirs['visual'] / 'character_data_schemaC_scenes.json'))
    
    return schema_c


def create_schema_c_with_scenes(video_path: str, characters: Dict,
                               face_tracker: FaceTracker,
                               scene_detector: SceneDetector) -> SchemaC:
    """Create Schema C with scene information"""
    import cv2
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    video_name = Path(video_path).stem
    schema_c = SchemaC(
        video_id=video_name,
        duration=duration,
        fps=fps,
        total_frames=total_frames
    )
    
    # Add character information with scene data
    for char_id, char_data in characters.items():
        if isinstance(char_data, dict):
            # Calculate scene-based statistics
            scene_appearances = defaultdict(int)
            scene_embeddings = {}
            
            for appearance in char_data.get('appearances', []):
                timestamp = appearance.get('timestamp', 0)
                scene_info = scene_detector.get_scene_at_time(timestamp)
                if scene_info:
                    scene_appearances[scene_info.scene_id] += 1
            
            # Create CharacterInfo with scene data
            char_info = CharacterInfo(
                character_id=f"char_{char_id}",
                num_appearances=char_data.get('total_frames', 0),
                first_appearance=char_data.get('first_appearance', 0),
                last_appearance=char_data.get('last_appearance', 0),
                total_screen_time=char_data.get('last_appearance', 0) - 
                                 char_data.get('first_appearance', 0),
                average_confidence=0.95,
                scene_appearances=dict(scene_appearances),
                scene_embeddings=scene_embeddings
            )
            
            schema_c.add_character(char_info)
            
            # Add face detections with scene information
            for i, appearance in enumerate(char_data.get('appearances', [])):
                scene_info = scene_detector.get_scene_at_time(
                    appearance.get('timestamp', 0)
                )
                
                detection = FaceDetection(
                    detection_id=f"{char_id}_{i}",
                    frame_number=appearance.get('frame_number', 0),
                    timestamp=appearance.get('timestamp', 0),
                    bbox=appearance.get('bbox', [0, 0, 1, 1]),
                    confidence=appearance.get('detection_score', 0.95),
                    character_id=f"char_{char_id}",
                    embedding=appearance.get('embedding', []),
                    quality_score=appearance.get('quality_score', 0.9),
                    scene_id=scene_info.scene_id if scene_info else None
                )
                
                schema_c.add_detection(detection)
    
    return schema_c


def apply_scene_aware_clustering(schema_c: SchemaC, scene_detector: SceneDetector,
                               output_dirs: Dict[str, Path]) -> Dict:
    """Apply scene-aware clustering to improve character grouping"""
    logger.info("Applying scene-aware character clustering...")
    
    clusterer = SceneAwareCharacterClusterer(
        intra_scene_threshold=0.65,
        inter_scene_threshold=0.75,
        min_cluster_size=3
    )
    
    # Prepare character data for clustering
    character_data = []
    for detection in schema_c.detections:
        char_data = {
            'character_id': detection.character_id,
            'embedding': detection.embedding,
            'frame_number': detection.frame_number,
            'first_appearance': detection.timestamp,
            'bbox': detection.bbox,
            'scene_id': detection.scene_id
        }
        character_data.append(char_data)
    
    # Perform clustering
    clustering_results = clusterer.cluster_characters_by_scene(
        character_data,
        scene_detector.scenes
    )
    
    # Save clustering results
    with open(output_dirs['visual'] / 'scene_clustering_results.json', 'w') as f:
        json.dump(clustering_results, f, indent=2)
    
    logger.info(f"Scene-aware clustering complete: "
               f"{len(clustering_results['global_characters'])} global characters identified")
    
    return clustering_results


def process_audio(video_path: str, output_dirs: Dict[str, Path],
                 whisper_model: str = 'base') -> Tuple[SchemaA, SchemaB]:
    """Process audio with transcription, emotion, and speaker diarization"""
    logger.info("Processing audio...")
    
    # Extract audio
    audio_extractor = AudioExtractor()
    audio_path = audio_extractor.extract_audio(
        video_path,
        output_path=str(output_dirs['audio'] / 'extracted_audio.wav')
    )
    
    # Process with Whisper
    whisper_config = WhisperConfig(model_size=whisper_model)
    whisper_processor = WhisperProcessor(whisper_config)
    schema_a = whisper_processor.process_audio(audio_path)
    
    # Add emotion
    emotion_processor = EmotionProcessor()
    emotion_processor.process_segments(schema_a.segments, audio_path)
    
    # Speaker diarization
    diarizer = SpeakerDiarizer()
    schema_b = diarizer.process_audio(audio_path)
    
    # Save schemas
    schema_a.save_json(str(output_dirs['audio'] / 'schema_a_transcription.json'))
    schema_b.save_json(str(output_dirs['audio'] / 'schema_b_speakers.json'))
    
    return schema_a, schema_b


def perform_fusion_with_scene_context(schema_a: SchemaA, schema_b: SchemaB,
                                    schema_c: SchemaC, clustering_results: Dict,
                                    output_dirs: Dict[str, Path]) -> SchemaD:
    """Perform fusion with scene-aware context"""
    logger.info("Performing scene-aware fusion...")
    
    # Update Schema C with clustering results
    enhanced_schema_c = update_schema_c_with_clustering(schema_c, clustering_results)
    
    # Perform fusion
    matcher = AdvancedCharacterMatcher()
    schema_d = matcher.match_characters_to_dialogue(
        schema_a, schema_b, enhanced_schema_c
    )
    
    # Save results
    schema_d.save_json(str(output_dirs['fusion'] / 'schema_d_matches_scene_aware.json'))
    
    # Generate report
    report_path = output_dirs['fusion'] / 'scene_aware_matching_report.md'
    generate_scene_aware_report(
        schema_d, clustering_results, report_path
    )
    
    return schema_d


def update_schema_c_with_clustering(schema_c: SchemaC, 
                                  clustering_results: Dict) -> SchemaC:
    """Update Schema C with improved clustering results"""
    # Map old character IDs to new global character IDs
    char_mapping = {}
    
    for global_char in clustering_results['global_characters']:
        new_id = global_char['character_id']
        for old_cluster_id in global_char['scene_clusters']:
            # Extract original character ID from cluster ID
            # Format: scene{scene_id}_char{char_id}
            parts = old_cluster_id.split('_')
            if len(parts) >= 2:
                old_char_id = parts[1].replace('char', '')
                char_mapping[f"char_{old_char_id}"] = new_id
    
    # Update detections with new character IDs
    for detection in schema_c.detections:
        if detection.character_id in char_mapping:
            detection.character_id = char_mapping[detection.character_id]
    
    # Update character info
    new_characters = {}
    for global_char in clustering_results['global_characters']:
        char_id = global_char['character_id']
        
        # Aggregate info from all merged characters
        total_detections = global_char['total_detections']
        temporal_span = global_char['temporal_span']
        
        char_info = CharacterInfo(
            character_id=char_id,
            num_appearances=total_detections,
            first_appearance=temporal_span['start'],
            last_appearance=temporal_span['end'],
            total_screen_time=temporal_span['duration'],
            average_confidence=0.95,
            representative_embeddings=[global_char.get('representative_embedding', [])],
            cross_scene_similarity=clustering_results['enhanced_profiles'][0].get(
                'cross_scene_similarity', 0.9
            ) if clustering_results.get('enhanced_profiles') else None,
            temporal_consistency=clustering_results['enhanced_profiles'][0].get(
                'temporal_consistency', 0.8
            ) if clustering_results.get('enhanced_profiles') else None
        )
        
        new_characters[char_id] = char_info
    
    schema_c.characters = new_characters
    return schema_c


def generate_scene_aware_report(schema_d: SchemaD, clustering_results: Dict,
                              output_path: Path):
    """Generate human-readable report with scene-aware insights"""
    report = []
    report.append("# Scene-Aware Character-Dialogue Matching Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Clustering statistics
    stats = clustering_results.get('statistics', {})
    report.append("## Scene-Aware Clustering Statistics\n")
    report.append(f"- Total scenes detected: {stats.get('total_scenes', 0)}\n")
    report.append(f"- Scene clusters before merging: {stats.get('total_scene_clusters', 0)}\n")
    report.append(f"- Global characters after merging: {stats.get('total_global_characters', 0)}\n")
    report.append(f"- Cluster reduction ratio: {stats.get('reduction_ratio', 0):.2f}\n")
    
    # Character insights
    report.append("\n## Character Scene Analysis\n")
    for global_char in clustering_results.get('global_characters', []):
        char_id = global_char['character_id']
        scenes = global_char['scenes']
        report.append(f"\n### {char_id}\n")
        report.append(f"- Appears in {len(scenes)} scenes: {scenes}\n")
        report.append(f"- Total detections: {global_char['total_detections']}\n")
        
    # Matching results
    report.append("\n## Dialogue Matching Results\n")
    report.append(f"- Total matches: {len(schema_d.matches)}\n")
    
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    for match in schema_d.matches:
        confidence_counts[match.confidence_level] += 1
    
    report.append(f"- High confidence: {confidence_counts['high']}\n")
    report.append(f"- Medium confidence: {confidence_counts['medium']}\n")
    report.append(f"- Low confidence: {confidence_counts['low']}\n")
    
    # Sample matches
    report.append("\n## Sample Character-Dialogue Matches\n")
    for i, match in enumerate(schema_d.matches[:10]):
        report.append(f"\n{i+1}. **{match.character_id}** @ {match.start_time:.2f}s:\n")
        report.append(f"   \"{match.dialogue_text}\"\n")
        report.append(f"   Confidence: {match.confidence_level} ({match.final_score:.2f})\n")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(report)
    
    logger.info(f"Report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run scene-aware character clustering pipeline"
    )
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument(
        "--output-dir",
        default="output/scene_aware",
        help="Base output directory"
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size"
    )
    parser.add_argument(
        "--target-frames",
        type=int,
        default=600,
        help="Target number of frames to extract"
    )
    parser.add_argument(
        "--scene-threshold",
        type=float,
        default=30.0,
        help="Scene detection threshold (higher = less sensitive)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.video_path):
        logger.error(f"Video file not found: {args.video_path}")
        return 1
    
    try:
        # Create output directories
        output_dirs = create_output_directories(args.output_dir)
        logger.info(f"Output directory: {output_dirs['session']}")
        
        # Step 1: Detect scenes
        scene_detector = process_scenes(
            args.video_path, output_dirs, args.scene_threshold
        )
        
        # Step 2: Process visual with scene-aware tracking
        schema_c = process_visual_with_scenes(
            args.video_path, output_dirs, scene_detector, args.target_frames
        )
        
        # Step 3: Apply scene-aware clustering
        clustering_results = apply_scene_aware_clustering(
            schema_c, scene_detector, output_dirs
        )
        
        # Step 4: Process audio
        schema_a, schema_b = process_audio(
            args.video_path, output_dirs, args.whisper_model
        )
        
        # Step 5: Perform fusion with scene context
        schema_d = perform_fusion_with_scene_context(
            schema_a, schema_b, schema_c, clustering_results, output_dirs
        )
        
        logger.info("Scene-aware pipeline completed successfully!")
        logger.info(f"Results saved to: {output_dirs['session']}")
        
        # Print summary
        print("\n" + "="*50)
        print("SCENE-AWARE PIPELINE SUMMARY")
        print("="*50)
        print(f"Scenes detected: {len(scene_detector.scenes)}")
        print(f"Global characters: {len(clustering_results['global_characters'])}")
        print(f"Total matches: {len(schema_d.matches)}")
        print(f"Output directory: {output_dirs['session']}")
        print("="*50)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())