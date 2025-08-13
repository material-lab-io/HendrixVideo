#!/usr/bin/env python3
"""
Analyze and visualize speaker diarization results from Schema B
"""

import json
from pathlib import Path
import sys
import os
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import SchemaB


def analyze_diarization(schema_path: str):
    """Analyze speaker diarization results"""
    
    # Load Schema B
    schema_b = SchemaB.load_json(schema_path)
    
    print(f"\n=== Speaker Diarization Analysis: {Path(schema_path).name} ===")
    print(f"Video ID: {schema_b.video_id}")
    print(f"Duration: {schema_b.duration:.1f}s ({schema_b.duration/60:.1f} minutes)")
    print(f"Number of speakers: {schema_b.num_speakers}")
    print(f"Total segments: {len(schema_b.segments)}")
    
    # Get speaker statistics
    stats = schema_b.get_speaker_stats()
    
    print("\n=== Speaker Statistics ===")
    for speaker_id, speaker_stats in sorted(stats.items()):
        print(f"\n{speaker_id}:")
        print(f"  Total speaking time: {speaker_stats['total_time']:.1f}s")
        print(f"  Percentage of total: {speaker_stats['percentage']:.1f}%")
        print(f"  Number of turns: {speaker_stats['num_segments']}")
        print(f"  Average turn duration: {speaker_stats['total_time']/speaker_stats['num_segments']:.1f}s")
    
    # Analyze turn-taking patterns
    print("\n=== Turn-Taking Analysis ===")
    
    # Count transitions
    transitions = defaultdict(int)
    for i in range(len(schema_b.segments) - 1):
        current_speaker = schema_b.segments[i].speaker_id
        next_speaker = schema_b.segments[i + 1].speaker_id
        if current_speaker != next_speaker:
            transitions[f"{current_speaker} -> {next_speaker}"] += 1
    
    print("\nSpeaker transitions:")
    for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {transition}: {count} times")
    
    # Find longest segments
    print("\n=== Longest Speaking Segments ===")
    sorted_segments = sorted(
        schema_b.segments, 
        key=lambda s: s.end_time - s.start_time, 
        reverse=True
    )
    
    for i, seg in enumerate(sorted_segments[:5]):
        duration = seg.end_time - seg.start_time
        print(
            f"{i+1}. {seg.speaker_id}: {duration:.1f}s "
            f"[{seg.start_time:.1f}s - {seg.end_time:.1f}s]"
        )
    
    # Create ASCII timeline visualization
    print("\n=== Timeline Visualization (first 60 seconds) ===")
    print("Time:    0    10   20   30   40   50   60")
    print("         |    |    |    |    |    |    |")
    
    # Create timeline for each speaker
    for speaker_id in sorted(stats.keys()):
        timeline = [' '] * 60  # One character per second
        
        for segment in schema_b.segments:
            if segment.speaker_id == speaker_id:
                start = int(segment.start_time)
                end = min(int(segment.end_time), 60)
                for i in range(start, end):
                    if i < 60:
                        timeline[i] = '█'
        
        print(f"{speaker_id[-2:]}: {''.join(timeline)}")
    
    # Analyze silence/overlap
    print("\n=== Silence and Overlap Analysis ===")
    
    total_silence = 0.0
    total_overlap = 0.0
    
    for i in range(len(schema_b.segments) - 1):
        current = schema_b.segments[i]
        next_seg = schema_b.segments[i + 1]
        
        gap = next_seg.start_time - current.end_time
        if gap > 0:
            total_silence += gap
        elif gap < 0:
            total_overlap += abs(gap)
    
    print(f"Total silence: {total_silence:.1f}s ({total_silence/schema_b.duration*100:.1f}%)")
    print(f"Total overlap: {total_overlap:.1f}s ({total_overlap/schema_b.duration*100:.1f}%)")
    
    # Summary
    print("\n=== Summary ===")
    if schema_b.num_speakers == 1:
        print("Monologue detected - single speaker throughout")
    elif schema_b.num_speakers == 2:
        print("Dialogue detected - two speakers")
        if len(transitions) > 0:
            avg_transitions = sum(transitions.values()) / len(transitions)
            print(f"Average transitions per pair: {avg_transitions:.1f}")
    else:
        print(f"Multi-party conversation - {schema_b.num_speakers} speakers")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_diarization.py <schema_b_json_file>")
        sys.exit(1)
    
    schema_path = sys.argv[1]
    
    if not Path(schema_path).exists():
        print(f"Error: File not found: {schema_path}")
        sys.exit(1)
    
    try:
        analyze_diarization(schema_path)
    except Exception as e:
        print(f"Error analyzing file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()