#!/usr/bin/env python3
"""
Comprehensive Schema Validation Script

This script validates that all schemas (A, B, C, D) are correctly populated
and contain the expected data structure and fields.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime

def validate_schema_a(schema_path: Path) -> Tuple[bool, List[str], Dict]:
    """Validate Schema A (transcription)"""
    errors = []
    stats = {}
    
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['video_id', 'duration', 'segments', 'created_at']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate segments
        if 'segments' in data:
            segments = data['segments']
            stats['total_segments'] = len(segments)
            
            if not segments:
                errors.append("No transcription segments found")
            else:
                # Check each segment
                total_duration = 0
                emotions_found = 0
                
                for i, seg in enumerate(segments):
                    seg_fields = ['segment_id', 'text', 'start_time', 'end_time', 'confidence']
                    for field in seg_fields:
                        if field not in seg:
                            errors.append(f"Segment {i} missing field: {field}")
                    
                    if 'start_time' in seg and 'end_time' in seg:
                        duration = seg['end_time'] - seg['start_time']
                        if duration <= 0:
                            errors.append(f"Segment {i} has invalid duration: {duration}")
                        total_duration += duration
                    
                    if seg.get('emotion'):
                        emotions_found += 1
                    
                    # Check text is not empty
                    if not seg.get('text', '').strip():
                        errors.append(f"Segment {i} has empty text")
                
                stats['total_dialogue_duration'] = total_duration
                stats['segments_with_emotion'] = emotions_found
                stats['emotion_coverage'] = f"{emotions_found/len(segments)*100:.1f}%"
        
        return len(errors) == 0, errors, stats
        
    except Exception as e:
        errors.append(f"Failed to load schema: {e}")
        return False, errors, stats

def validate_schema_b(schema_path: Path) -> Tuple[bool, List[str], Dict]:
    """Validate Schema B (speaker diarization)"""
    errors = []
    stats = {}
    
    if not schema_path.exists():
        stats['status'] = 'Not generated (optional)'
        return True, errors, stats
    
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['video_id', 'duration', 'num_speakers', 'segments']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if 'segments' in data:
            segments = data['segments']
            stats['total_segments'] = len(segments)
            stats['num_speakers'] = data.get('num_speakers', 0)
            
            # Check each segment
            speakers = set()
            for i, seg in enumerate(segments):
                seg_fields = ['segment_id', 'speaker_id', 'start_time', 'end_time']
                for field in seg_fields:
                    if field not in seg:
                        errors.append(f"Segment {i} missing field: {field}")
                
                if 'speaker_id' in seg:
                    speakers.add(seg['speaker_id'])
            
            stats['unique_speakers'] = len(speakers)
            
            if len(speakers) != data.get('num_speakers', 0):
                errors.append(f"Speaker count mismatch: {len(speakers)} vs {data.get('num_speakers')}")
        
        return len(errors) == 0, errors, stats
        
    except Exception as e:
        errors.append(f"Failed to load schema: {e}")
        return False, errors, stats

def validate_schema_c(schema_path: Path) -> Tuple[bool, List[str], Dict]:
    """Validate Schema C (visual/character data)"""
    errors = []
    stats = {}
    
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['video_id', 'duration', 'fps', 'total_frames', 'characters', 'detections']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate characters
        if 'characters' in data:
            characters = data['characters']
            stats['total_characters'] = len(characters)
            
            if not characters:
                errors.append("No characters found")
            else:
                for char_id, char_data in characters.items():
                    char_fields = ['character_id', 'num_appearances', 'appearance_segments']
                    for field in char_fields:
                        if field not in char_data:
                            errors.append(f"Character {char_id} missing field: {field}")
                    
                    # Check embeddings
                    if 'representative_embeddings' in char_data:
                        embeddings = char_data['representative_embeddings']
                        if not embeddings:
                            errors.append(f"Character {char_id} has no embeddings")
                        stats[f'char_{char_id}_embeddings'] = len(embeddings)
        
        # Validate detections
        if 'detections' in data:
            detections = data['detections']
            stats['total_detections'] = len(detections)
            
            # Check temporal distribution
            if detections:
                timestamps = [d.get('timestamp', 0) for d in detections]
                stats['detection_time_range'] = f"{min(timestamps):.1f}s - {max(timestamps):.1f}s"
                
                # Check detection fields
                for i, det in enumerate(detections[:5]):  # Check first 5
                    # Required fields
                    required_det_fields = ['frame_number', 'timestamp', 'character_id', 'bbox', 'confidence']
                    for field in required_det_fields:
                        if field not in det:
                            errors.append(f"Detection {i} missing required field: {field}")
                    
                    # Optional fields that we just note if missing
                    optional_det_fields = ['track_id', 'detection_id', 'embedding', 'quality_score']
                    for field in optional_det_fields:
                        if field not in det:
                            # Just log as info, not error
                            pass
        
        return len(errors) == 0, errors, stats
        
    except Exception as e:
        errors.append(f"Failed to load schema: {e}")
        return False, errors, stats

def validate_schema_d(schema_path: Path) -> Tuple[bool, List[str], Dict]:
    """Validate Schema D (character-dialogue matches)"""
    errors = []
    stats = {}
    
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['video_id', 'duration', 'matches', 'unmatched_dialogues']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate matches
        if 'matches' in data:
            matches = data['matches']
            stats['total_matches'] = len(matches)
            
            if not matches:
                errors.append("No matches found")
            else:
                # Analyze match distribution
                char_dialogue_count = {}
                confidence_scores = []
                
                for i, match in enumerate(matches):
                    match_fields = ['match_id', 'character_id', 'dialogue']
                    for field in match_fields:
                        if field not in match:
                            errors.append(f"Match {i} missing field: {field}")
                    
                    char_id = match.get('character_id')
                    if char_id:
                        char_dialogue_count[char_id] = char_dialogue_count.get(char_id, 0) + 1
                    
                    # Check matching score
                    if 'matching_score' in match and match['matching_score']:
                        if 'final_score' in match['matching_score']:
                            confidence_scores.append(match['matching_score']['final_score'])
                
                stats['character_distribution'] = char_dialogue_count
                if confidence_scores:
                    stats['avg_confidence'] = f"{np.mean(confidence_scores):.3f}"
                    stats['confidence_range'] = f"{min(confidence_scores):.3f} - {max(confidence_scores):.3f}"
        
        # Check unmatched
        if 'unmatched_dialogues' in data:
            stats['unmatched_count'] = len(data['unmatched_dialogues'])
            
            total_dialogues = stats['total_matches'] + stats['unmatched_count']
            if total_dialogues > 0:
                stats['match_rate'] = f"{stats['total_matches']/total_dialogues*100:.1f}%"
        
        return len(errors) == 0, errors, stats
        
    except Exception as e:
        errors.append(f"Failed to load schema: {e}")
        return False, errors, stats

def validate_session(session_dir: Path) -> Dict:
    """Validate all schemas in a session"""
    results = {
        'session': session_dir.name,
        'timestamp': datetime.now().isoformat(),
        'schemas': {}
    }
    
    # Schema A
    audio_dirs = list((session_dir / "audio_output").glob("*"))
    if audio_dirs:
        audio_dir = audio_dirs[0]
        schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
        if schema_a_path.exists():
            valid, errors, stats = validate_schema_a(schema_a_path)
            results['schemas']['A'] = {
                'valid': valid,
                'errors': errors,
                'stats': stats,
                'path': str(schema_a_path)
            }
        else:
            results['schemas']['A'] = {'valid': False, 'errors': ['Schema file not found']}
    else:
        results['schemas']['A'] = {'valid': False, 'errors': ['Audio output directory not found']}
    
    # Schema B
    if audio_dirs:
        schema_b_path = audio_dirs[0] / "schemas" / "schema_b_speakers.json"
        valid, errors, stats = validate_schema_b(schema_b_path)
        results['schemas']['B'] = {
            'valid': valid,
            'errors': errors,
            'stats': stats,
            'path': str(schema_b_path) if schema_b_path.exists() else 'Not generated'
        }
    else:
        results['schemas']['B'] = {'valid': True, 'stats': {'status': 'Not generated (audio dir missing)'}}
    
    # Schema C
    schema_c_path = session_dir / "visual_output" / "character_data_schemaC.json"
    if schema_c_path.exists():
        valid, errors, stats = validate_schema_c(schema_c_path)
        results['schemas']['C'] = {
            'valid': valid,
            'errors': errors,
            'stats': stats,
            'path': str(schema_c_path)
        }
    else:
        results['schemas']['C'] = {'valid': False, 'errors': ['Schema file not found']}
    
    # Schema D
    schema_d_path = session_dir / "fusion_output" / "schema_d_matches.json"
    if schema_d_path.exists():
        valid, errors, stats = validate_schema_d(schema_d_path)
        results['schemas']['D'] = {
            'valid': valid,
            'errors': errors,
            'stats': stats,
            'path': str(schema_d_path)
        }
    else:
        results['schemas']['D'] = {'valid': False, 'errors': ['Schema file not found']}
    
    # Overall validation
    results['all_valid'] = all(s.get('valid', False) for s in results['schemas'].values() if s)
    
    return results

def print_validation_report(results: Dict):
    """Print a formatted validation report"""
    print("\n" + "="*60)
    print(f"SCHEMA VALIDATION REPORT")
    print(f"Session: {results['session']}")
    print("="*60)
    
    for schema_name, schema_data in results['schemas'].items():
        print(f"\n## Schema {schema_name}")
        print(f"Valid: {'✅' if schema_data.get('valid') else '❌'}")
        
        if schema_data.get('errors'):
            print(f"Errors: {len(schema_data['errors'])}")
            for error in schema_data['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
        
        if schema_data.get('stats'):
            print("Statistics:")
            for key, value in schema_data['stats'].items():
                if isinstance(value, dict):
                    print(f"  - {key}:")
                    for k, v in value.items():
                        print(f"    - {k}: {v}")
                else:
                    print(f"  - {key}: {value}")
    
    print(f"\n{'='*60}")
    print(f"Overall Validation: {'✅ PASS' if results['all_valid'] else '❌ FAIL'}")
    print(f"{'='*60}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_all_schemas.py <session_directory>")
        sys.exit(1)
    
    session_dir = Path(sys.argv[1])
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}")
        sys.exit(1)
    
    # Validate all schemas
    results = validate_session(session_dir)
    
    # Print report
    print_validation_report(results)
    
    # Save detailed report
    report_path = session_dir / "schema_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Detailed report saved to: {report_path}")
    
    return 0 if results['all_valid'] else 1

if __name__ == "__main__":
    sys.exit(main())