#!/usr/bin/env python3
"""
Display All Schemas Script

This script displays the content of all schemas (A, B, C, D) in a readable format
"""

import json
import sys
from pathlib import Path
from typing import Dict
import pandas as pd


def display_schema_a(schema_path: Path):
    """Display Schema A (transcription)"""
    print("\n" + "="*80)
    print("SCHEMA A - TRANSCRIPTION DATA")
    print("="*80)
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    print(f"\nVideo ID: {data['video_id']}")
    print(f"Duration: {data['duration']:.1f} seconds")
    print(f"Total Segments: {len(data['segments'])}")
    
    if 'metadata' in data:
        print(f"\nMetadata:")
        for key, value in data['metadata'].items():
            print(f"  - {key}: {value}")
    
    print(f"\nFirst 5 Dialogue Segments:")
    for i, seg in enumerate(data['segments'][:5]):
        print(f"\n[{i+1}] {seg['segment_id']} ({seg['start_time']:.1f}s - {seg['end_time']:.1f}s)")
        print(f"    Text: \"{seg['text'][:80]}...\"" if len(seg['text']) > 80 else f"    Text: \"{seg['text']}\"")
        print(f"    Confidence: {seg['confidence']:.3f}")
        if seg.get('emotion'):
            print(f"    Emotion: {seg['emotion']} (confidence: {seg.get('emotion_confidence', 0):.3f})")


def display_schema_b(schema_path: Path):
    """Display Schema B (speaker diarization)"""
    print("\n" + "="*80)
    print("SCHEMA B - SPEAKER DIARIZATION")
    print("="*80)
    
    if not schema_path.exists():
        print("\nSchema B not generated (optional)")
        return
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    print(f"\nVideo ID: {data['video_id']}")
    print(f"Duration: {data['duration']:.1f} seconds")
    print(f"Number of Speakers: {data['num_speakers']}")
    print(f"Total Segments: {len(data['segments'])}")
    
    # Analyze speaker distribution
    speaker_times = {}
    for seg in data['segments']:
        speaker = seg['speaker_id']
        duration = seg['end_time'] - seg['start_time']
        speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
    
    print(f"\nSpeaker Distribution:")
    for speaker, time in sorted(speaker_times.items()):
        percentage = (time / data['duration']) * 100
        print(f"  - {speaker}: {time:.1f}s ({percentage:.1f}%)")
    
    print(f"\nFirst 5 Speaker Segments:")
    for i, seg in enumerate(data['segments'][:5]):
        print(f"  [{i+1}] {seg['speaker_id']} ({seg['start_time']:.1f}s - {seg['end_time']:.1f}s)")


def display_schema_c(schema_path: Path):
    """Display Schema C (visual/character data)"""
    print("\n" + "="*80)
    print("SCHEMA C - VISUAL/CHARACTER DATA")
    print("="*80)
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    print(f"\nVideo ID: {data['video_id']}")
    print(f"Duration: {data['duration']:.1f} seconds")
    print(f"FPS: {data['fps']}")
    print(f"Total Frames: {data['total_frames']}")
    print(f"Total Detections: {len(data.get('detections', []))}")
    print(f"Unique Characters: {len(data.get('characters', {}))}")
    
    print(f"\nCharacter Summary:")
    characters = data.get('characters', {})
    
    # Create a summary table
    char_data = []
    for char_id, char_info in sorted(characters.items(), key=lambda x: x[1].get('num_appearances', 0), reverse=True):
        char_data.append({
            'ID': char_id,
            'Appearances': char_info.get('num_appearances', 0),
            'First Seen': f"{char_info.get('first_appearance', 0):.1f}s",
            'Last Seen': f"{char_info.get('last_appearance', 0):.1f}s",
            'Screen Time': f"{char_info.get('total_screen_time', 0):.1f}s",
            'Embeddings': len(char_info.get('representative_embeddings', [])),
            'Confidence': f"{char_info.get('average_confidence', 0):.3f}"
        })
    
    if char_data:
        df = pd.DataFrame(char_data)
        print(df.to_string(index=False))
    
    # Show temporal coverage
    if data.get('detections'):
        timestamps = [d['timestamp'] for d in data['detections']]
        print(f"\nTemporal Coverage:")
        print(f"  - First detection: {min(timestamps):.1f}s")
        print(f"  - Last detection: {max(timestamps):.1f}s")
        print(f"  - Coverage: {(max(timestamps) - min(timestamps)) / data['duration'] * 100:.1f}%")


def display_schema_d(schema_path: Path):
    """Display Schema D (character-dialogue matches)"""
    print("\n" + "="*80)
    print("SCHEMA D - CHARACTER-DIALOGUE MATCHES")
    print("="*80)
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    print(f"\nVideo ID: {data['video_id']}")
    print(f"Duration: {data['duration']:.1f} seconds")
    print(f"Total Matches: {len(data['matches'])}")
    print(f"Unmatched Dialogues: {len(data['unmatched_dialogues'])}")
    
    total_dialogues = len(data['matches']) + len(data['unmatched_dialogues'])
    match_rate = len(data['matches']) / total_dialogues * 100 if total_dialogues > 0 else 0
    print(f"Match Rate: {match_rate:.1f}%")
    
    # Character distribution
    char_counts = {}
    confidence_scores = []
    
    for match in data['matches']:
        char_id = match['character_id']
        char_counts[char_id] = char_counts.get(char_id, 0) + 1
        
        if 'matching_score' in match and match['matching_score']:
            if 'final_score' in match['matching_score']:
                confidence_scores.append(match['matching_score']['final_score'])
    
    print(f"\nCharacter Dialogue Distribution:")
    for char_id, count in sorted(char_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - Character {char_id}: {count} dialogues")
    
    if confidence_scores:
        import numpy as np
        print(f"\nConfidence Statistics:")
        print(f"  - Average: {np.mean(confidence_scores):.3f}")
        print(f"  - Min: {np.min(confidence_scores):.3f}")
        print(f"  - Max: {np.max(confidence_scores):.3f}")
        print(f"  - Std Dev: {np.std(confidence_scores):.3f}")
    
    print(f"\nFirst 5 Matches:")
    for i, match in enumerate(data['matches'][:5]):
        dialogue = match['dialogue']
        print(f"\n[{i+1}] Character {match['character_id']} ({dialogue['start_time']:.1f}s - {dialogue['end_time']:.1f}s)")
        print(f"    Text: \"{dialogue['text'][:80]}...\"" if len(dialogue['text']) > 80 else f"    Text: \"{dialogue['text']}\"")
        if match.get('matching_score'):
            print(f"    Confidence: {match['matching_score'].get('final_score', 0):.3f}")
            if match['matching_score'].get('heuristic_scores'):
                scores = match['matching_score']['heuristic_scores']
                print(f"    Scores: temporal={scores.get('temporal', 0):.2f}, "
                      f"continuity={scores.get('continuity', 0):.2f}, "
                      f"position={scores.get('position', 0):.2f}")
    
    if data['unmatched_dialogues']:
        print(f"\nFirst 3 Unmatched Dialogues:")
        for i, dialogue in enumerate(data['unmatched_dialogues'][:3]):
            print(f"  [{i+1}] \"{dialogue['text'][:60]}...\" ({dialogue['start_time']:.1f}s)")


def display_session(session_dir: Path):
    """Display all schemas in a session"""
    print(f"\n{'='*80}")
    print(f"SESSION: {session_dir.name}")
    print(f"{'='*80}")
    
    # Schema A
    audio_dirs = list((session_dir / "audio_output").glob("*"))
    if audio_dirs:
        schema_a_path = audio_dirs[0] / "schemas" / "schema_a_transcription.json"
        if schema_a_path.exists():
            display_schema_a(schema_a_path)
    
    # Schema B
    if audio_dirs:
        schema_b_path = audio_dirs[0] / "schemas" / "schema_b_speakers.json"
        display_schema_b(schema_b_path)
    
    # Schema C
    schema_c_path = session_dir / "visual_output" / "character_data_schemaC.json"
    if schema_c_path.exists():
        display_schema_c(schema_c_path)
    
    # Schema D
    schema_d_path = session_dir / "fusion_output" / "schema_d_matches.json"
    if schema_d_path.exists():
        display_schema_d(schema_d_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python display_all_schemas.py <session_directory>")
        sys.exit(1)
    
    session_dir = Path(sys.argv[1])
    if not session_dir.exists():
        print(f"Error: Session directory not found: {session_dir}")
        sys.exit(1)
    
    display_session(session_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())