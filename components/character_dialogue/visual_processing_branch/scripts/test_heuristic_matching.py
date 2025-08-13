#!/usr/bin/env python3
"""
Test Heuristic Matching Implementation

This script tests the heuristic rules for character-dialogue matching
using real data from our schemas.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.schemas import SchemaA, SchemaB, SchemaC, TranscriptionSegment
from src.fusion.heuristic_matcher import HeuristicMatcher, HeuristicConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schemas(audio_dir: Path, visual_dir: Path) -> tuple:
    """Load Schema A, B, and C from directories"""
    
    # Load Schema A (with emotions)
    schema_a_path = audio_dir / "schemas" / "schema_a_with_emotions.json"
    if not schema_a_path.exists():
        schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
    
    with open(schema_a_path, 'r') as f:
        schema_a_data = json.load(f)
    
    # Create SchemaA from dict
    schema_a = SchemaA(
        video_id=schema_a_data['video_id'],
        duration=schema_a_data['duration']
    )
    for seg_data in schema_a_data['segments']:
        segment = TranscriptionSegment(
            segment_id=seg_data['segment_id'],
            text=seg_data['text'],
            start_time=seg_data['start_time'],
            end_time=seg_data['end_time'],
            confidence=seg_data['confidence'],
            emotion=seg_data.get('emotion'),
            emotion_confidence=seg_data.get('emotion_confidence'),
            source=seg_data.get('source', 'whisper')
        )
        schema_a.add_segment(segment)
    
    # Load Schema B
    schema_b_path = audio_dir / "schemas" / "schema_b_speakers.json"
    schema_b = None
    if schema_b_path.exists():
        with open(schema_b_path, 'r') as f:
            schema_b_data = json.load(f)
        
        # Create SchemaB from dict
        from src.schemas import SpeakerSegment
        schema_b = SchemaB(
            video_id=schema_b_data['video_id'],
            duration=schema_b_data['duration'],
            num_speakers=schema_b_data['num_speakers']
        )
        for seg_data in schema_b_data['segments']:
            segment = SpeakerSegment(
                speaker_id=seg_data['speaker_id'],
                start_time=seg_data['start_time'],
                end_time=seg_data['end_time'],
                confidence=seg_data.get('confidence', 1.0)
            )
            schema_b.add_segment(segment)
    
    # Load Schema C
    schema_c_path = visual_dir / "schema_c_enhanced.json"
    if not schema_c_path.exists():
        # Try standard pipeline output
        schema_c_path = visual_dir / "schemas" / "schema_c_characters.json"
    
    with open(schema_c_path, 'r') as f:
        schema_c_data = json.load(f)
    # Note: We need to create from_dict method for SchemaC
    schema_c = SchemaC(
        video_id=schema_c_data['video_id'],
        duration=schema_c_data['duration'],
        fps=schema_c_data['fps'],
        total_frames=schema_c_data['total_frames']
    )
    
    # Load detections and characters
    for det_data in schema_c_data.get('detections', []):
        from src.schemas import FaceDetection
        detection = FaceDetection(
            detection_id=det_data['detection_id'],
            frame_number=det_data['frame_number'],
            timestamp=det_data['timestamp'],
            bbox=det_data['bbox'],
            confidence=det_data['confidence'],
            character_id=det_data.get('character_id'),
            embedding=det_data.get('embedding'),
            quality_score=det_data.get('quality_score'),
            attributes=det_data.get('attributes')
        )
        schema_c.add_detection(detection)
    
    for char_id, char_data in schema_c_data.get('characters', {}).items():
        from src.schemas import CharacterInfo
        character = CharacterInfo(
            character_id=char_id,
            num_appearances=char_data['num_appearances'],
            first_appearance=char_data['first_appearance'],
            last_appearance=char_data['last_appearance'],
            total_screen_time=char_data['total_screen_time'],
            average_confidence=char_data['average_confidence'],
            representative_embeddings=char_data.get('representative_embeddings', []),
            appearance_segments=char_data.get('appearance_segments', []),
            attributes=char_data.get('attributes')
        )
        schema_c.add_character(character)
    
    return schema_a, schema_b, schema_c


def test_heuristic_matching(schema_a: SchemaA, schema_b: Optional[SchemaB], schema_c: SchemaC):
    """Test heuristic matching on loaded schemas"""
    
    logger.info("Testing heuristic matching...")
    logger.info(f"Schema A: {len(schema_a.segments)} dialogue segments")
    if schema_b:
        logger.info(f"Schema B: {len(schema_b.segments)} speaker segments")
    else:
        logger.info("Schema B: Not available (speaker diarization skipped)")
    logger.info(f"Schema C: {len(schema_c.characters)} characters, {len(schema_c.detections)} detections")
    
    # Initialize matcher
    matcher = HeuristicMatcher()
    
    # Test matching for first few dialogue segments
    results = []
    
    for i, dialogue in enumerate(schema_a.segments[:10]):  # Test first 10 dialogues
        logger.info(f"\nTesting dialogue {i+1}: '{dialogue.text[:50]}...'")
        logger.info(f"Time: {dialogue.start_time:.2f}s - {dialogue.end_time:.2f}s")
        
        # Find corresponding speaker segment
        speaker_segment = None
        if schema_b:
            for speaker in schema_b.segments:
                if (speaker.start_time <= dialogue.start_time <= speaker.end_time or
                    speaker.start_time <= dialogue.end_time <= speaker.end_time):
                    speaker_segment = speaker
                    break
            
            if speaker_segment:
                logger.info(f"Found speaker: {speaker_segment.speaker_id}")
        
        # Calculate scores for each character
        character_scores = {}
        
        for char_id, char_info in schema_c.characters.items():
            scores = matcher.calculate_heuristic_scores(
                dialogue, char_id, schema_c, speaker_segment
            )
            
            if scores:
                best_score = matcher.get_best_heuristic_score(scores)
                character_scores[char_id] = {
                    'scores': scores,
                    'best_score': best_score,
                    'confidence': matcher.determine_confidence_level(best_score)
                }
                
                logger.info(f"\nCharacter {char_id} scores:")
                for rule, score in scores.items():
                    logger.info(f"  {rule}: {score:.3f}")
                logger.info(f"  Best score: {best_score:.3f} ({character_scores[char_id]['confidence']})")
        
        results.append({
            'dialogue': dialogue.text,
            'time': f"{dialogue.start_time:.2f}-{dialogue.end_time:.2f}",
            'character_scores': character_scores,
            'best_match': max(character_scores.items(), 
                            key=lambda x: x[1]['best_score'])[0] if character_scores else None
        })
    
    return results


def generate_report(results: list, output_path: Path):
    """Generate test report"""
    
    with open(output_path, 'w') as f:
        f.write("# Heuristic Matching Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Dialogues tested:** {len(results)}\n\n")
        
        f.write("## Matching Results\n\n")
        
        for i, result in enumerate(results):
            f.write(f"### Dialogue {i+1}\n")
            f.write(f"**Text:** \"{result['dialogue'][:100]}...\"\n")
            f.write(f"**Time:** {result['time']}s\n\n")
            
            if result['character_scores']:
                f.write("**Character Scores:**\n")
                for char_id, char_data in result['character_scores'].items():
                    f.write(f"\n**Character {char_id}** ({char_data['confidence']}):\n")
                    for rule, score in char_data['scores'].items():
                        f.write(f"- {rule}: {score:.3f}\n")
                    f.write(f"- **Best score:** {char_data['best_score']:.3f}\n")
                
                f.write(f"\n**Best Match:** Character {result['best_match']}\n")
            else:
                f.write("**No character matches found**\n")
            
            f.write("\n---\n\n")
        
        # Summary statistics
        f.write("## Summary\n\n")
        matched = sum(1 for r in results if r['best_match'] is not None)
        f.write(f"- Dialogues with matches: {matched}/{len(results)}\n")
        
        # Confidence distribution
        confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
        for result in results:
            if result['best_match'] and result['character_scores']:
                conf = result['character_scores'][result['best_match']]['confidence']
                confidence_counts[conf] += 1
        
        f.write(f"- High confidence: {confidence_counts['high']}\n")
        f.write(f"- Medium confidence: {confidence_counts['medium']}\n")
        f.write(f"- Low confidence: {confidence_counts['low']}\n")
    
    logger.info(f"Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test heuristic matching")
    parser.add_argument("--audio-dir", required=True, help="Audio pipeline output directory")
    parser.add_argument("--visual-dir", required=True, help="Visual pipeline output directory")
    parser.add_argument("--output", default="output/fusion_test", help="Output directory")
    
    args = parser.parse_args()
    
    # Convert to paths
    audio_dir = Path(args.audio_dir)
    visual_dir = Path(args.visual_dir)
    
    if not audio_dir.exists() or not visual_dir.exists():
        logger.error("Input directories not found!")
        return
    
    # Load schemas
    try:
        schema_a, schema_b, schema_c = load_schemas(audio_dir, visual_dir)
    except Exception as e:
        logger.error(f"Failed to load schemas: {e}")
        return
    
    # Run tests
    results = test_heuristic_matching(schema_a, schema_b, schema_c)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    results_path = output_dir / "heuristic_test_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate report
    report_path = output_dir / "heuristic_test_report.md"
    generate_report(results, report_path)
    
    print("\n" + "="*60)
    print("HEURISTIC MATCHING TEST COMPLETE")
    print("="*60)
    print(f"Results saved to: {results_path}")
    print(f"Report saved to: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()