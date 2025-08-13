#!/usr/bin/env python3
"""
Test Complete Character-Dialogue Fusion Pipeline

This script tests the complete fusion pipeline including:
1. Heuristic matching
2. LLM-based analysis  
3. Final fusion scoring
4. Schema D generation
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

from src.schemas import SchemaA, SchemaB, SchemaC, SchemaD, TranscriptionSegment
from src.fusion.character_dialogue_matcher import CharacterDialogueMatcher, FusionConfig

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
    
    # Load Schema B (if available)
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
                segment_id=seg_data['segment_id'],
                speaker_id=seg_data['speaker_id'],
                start_time=seg_data['start_time'],
                end_time=seg_data['end_time'],
                confidence=seg_data.get('confidence', 1.0)
            )
            schema_b.add_segment(segment)
    
    # Load Schema C - check multiple possible paths
    schema_c_path = visual_dir / "character_data_schemaC.json"
    if not schema_c_path.exists():
        schema_c_path = visual_dir / "schema_c_enhanced.json"
        if not schema_c_path.exists():
            # Try standard pipeline output
            schema_c_path = visual_dir / "schemas" / "schema_c_characters.json"
    
    with open(schema_c_path, 'r') as f:
        schema_c_data = json.load(f)
    
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


def test_fusion_pipeline(schema_a: SchemaA, schema_b: Optional[SchemaB], schema_c: SchemaC, 
                        config: FusionConfig) -> SchemaD:
    """Test the complete fusion pipeline"""
    
    logger.info("="*60)
    logger.info("TESTING COMPLETE FUSION PIPELINE")
    logger.info("="*60)
    
    # Create matcher
    matcher = CharacterDialogueMatcher(config)
    
    # Perform matching
    schema_d = matcher.match_schemas(schema_a, schema_c, schema_b)
    
    # Log results
    logger.info(f"\nMatching Results:")
    logger.info(f"- Total dialogues: {len(schema_a.segments)}")
    logger.info(f"- Matched: {len(schema_d.matches)}")
    logger.info(f"- Unmatched: {len(schema_d.unmatched_dialogues)}")
    logger.info(f"- Matching rate: {schema_d.matching_summary['matching_rate']:.2%}")
    
    # Log confidence distribution
    conf_dist = schema_d.matching_summary['confidence_distribution']
    logger.info(f"\nConfidence Distribution:")
    logger.info(f"- High: {conf_dist['high']}")
    logger.info(f"- Medium: {conf_dist['medium']}")  
    logger.info(f"- Low: {conf_dist['low']}")
    
    # Log character dialogue counts
    logger.info(f"\nCharacter Dialogue Assignments:")
    for char_id, count in schema_d.matching_summary['character_dialogue_counts'].items():
        logger.info(f"- Character {char_id}: {count} dialogues")
    
    return schema_d


def generate_detailed_report(schema_d: SchemaD, output_path: Path):
    """Generate detailed fusion report"""
    
    with open(output_path, 'w') as f:
        f.write("# Character-Dialogue Fusion Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Video ID:** {schema_d.video_id}\n")
        f.write(f"**Duration:** {schema_d.duration:.1f}s\n\n")
        
        # Summary statistics
        f.write("## Summary Statistics\n\n")
        summary = schema_d.matching_summary
        f.write(f"- **Total dialogues:** {summary['total_dialogues']}\n")
        f.write(f"- **Matched:** {summary['matched_dialogues']} ({summary['matching_rate']:.1%})\n")
        f.write(f"- **Unmatched:** {summary['unmatched_dialogues']}\n")
        f.write(f"- **Average confidence:** {summary['average_confidence']:.2f}\n\n")
        
        # Confidence distribution
        f.write("### Confidence Distribution\n\n")
        conf = summary['confidence_distribution']
        f.write(f"- High confidence: {conf['high']}\n")
        f.write(f"- Medium confidence: {conf['medium']}\n")
        f.write(f"- Low confidence: {conf['low']}\n\n")
        
        # Character assignments
        f.write("### Character Dialogue Counts\n\n")
        for char_id, count in summary['character_dialogue_counts'].items():
            f.write(f"- Character {char_id}: {count} dialogues\n")
        f.write("\n")
        
        # Detailed matches
        f.write("## Detailed Matches\n\n")
        
        # Group by confidence level
        high_conf = [m for m in schema_d.matches 
                    if m.matching_score and m.matching_score.confidence_level == 'high']
        medium_conf = [m for m in schema_d.matches 
                      if m.matching_score and m.matching_score.confidence_level == 'medium']
        low_conf = [m for m in schema_d.matches 
                   if m.matching_score and m.matching_score.confidence_level == 'low']
        
        # High confidence matches
        if high_conf:
            f.write("### High Confidence Matches\n\n")
            for match in high_conf[:5]:  # Show first 5
                f.write(f"**[{match.dialogue_segment.start_time:.1f}s - {match.dialogue_segment.end_time:.1f}s]** ")
                f.write(f"Character {match.character_id}: \"{match.dialogue_segment.text[:80]}...\"\n")
                f.write(f"- Score: {match.matching_score.final_score:.2f}\n")
                f.write(f"- Reasoning: {match.matching_score.reasoning}\n\n")
        
        # Medium confidence matches
        if medium_conf:
            f.write("### Medium Confidence Matches\n\n")
            for match in medium_conf[:5]:  # Show first 5
                f.write(f"**[{match.dialogue_segment.start_time:.1f}s - {match.dialogue_segment.end_time:.1f}s]** ")
                f.write(f"Character {match.character_id}: \"{match.dialogue_segment.text[:80]}...\"\n")
                f.write(f"- Score: {match.matching_score.final_score:.2f}\n")
                f.write(f"- Reasoning: {match.matching_score.reasoning}\n\n")
        
        # Unmatched dialogues
        if schema_d.unmatched_dialogues:
            f.write("### Unmatched Dialogues\n\n")
            for dialogue in schema_d.unmatched_dialogues[:5]:  # Show first 5
                f.write(f"**[{dialogue.start_time:.1f}s - {dialogue.end_time:.1f}s]** ")
                f.write(f"\"{dialogue.text[:80]}...\"\n\n")
        
        # Technical details
        f.write("## Technical Details\n\n")
        f.write("### Fusion Configuration\n\n")
        fusion_config = schema_d.metadata.get('fusion_config', {})
        f.write(f"- Heuristic weight: {fusion_config.get('heuristic_weight', 'N/A')}\n")
        f.write(f"- LLM weight: {fusion_config.get('llm_weight', 'N/A')}\n")
        f.write(f"- LLM enabled: {fusion_config.get('use_llm', False)}\n\n")
        
        f.write("### Source Schemas\n\n")
        sources = schema_d.metadata.get('source_schemas', {})
        for schema_name, info in sources.items():
            f.write(f"- {schema_name}: {info}\n")
    
    logger.info(f"Detailed report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test complete fusion pipeline")
    parser.add_argument("--audio-dir", required=True, help="Audio pipeline output directory")
    parser.add_argument("--visual-dir", required=True, help="Visual pipeline output directory") 
    parser.add_argument("--output", default="output/fusion_test", help="Output directory")
    parser.add_argument("--use-llm", action="store_true", help="Enable LLM analysis (simulated)")
    parser.add_argument("--heuristic-weight", type=float, default=0.4, 
                       help="Weight for heuristic scores (default: 0.4)")
    parser.add_argument("--llm-weight", type=float, default=0.6,
                       help="Weight for LLM scores (default: 0.6)")
    
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
    
    # Configure fusion
    config = FusionConfig(
        heuristic_weight=args.heuristic_weight,
        llm_weight=args.llm_weight,
        use_llm=args.use_llm,
        use_speaker_diarization=(schema_b is not None)
    )
    
    # Run fusion pipeline
    schema_d = test_fusion_pipeline(schema_a, schema_b, schema_c, config)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output) / f"fusion_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save Schema D
    schema_d_path = output_dir / "schema_d_matches.json"
    with open(schema_d_path, 'w') as f:
        json.dump(schema_d.to_dict(), f, indent=2)
    logger.info(f"Schema D saved to: {schema_d_path}")
    
    # Generate report
    report_path = output_dir / "fusion_report.md"
    generate_detailed_report(schema_d, report_path)
    
    # Print final summary
    print("\n" + "="*60)
    print("CHARACTER-DIALOGUE FUSION COMPLETE")
    print("="*60)
    print(f"Matched: {len(schema_d.matches)}/{len(schema_a.segments)} dialogues")
    print(f"Average confidence: {schema_d.matching_summary['average_confidence']:.2f}")
    print(f"\nOutputs:")
    print(f"- Schema D: {schema_d_path}")
    print(f"- Report: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()