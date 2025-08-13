#!/usr/bin/env python3
"""
Analyze emotion distribution in Schema A files
"""

import json
from pathlib import Path
import sys
import os
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import SchemaA


def analyze_emotions(schema_path: str):
    """Analyze emotion distribution in a Schema A file"""
    
    # Load schema
    schema_a = SchemaA.load_json(schema_path)
    
    print(f"\n=== Emotion Analysis: {Path(schema_path).name} ===")
    print(f"Video ID: {schema_a.video_id}")
    print(f"Duration: {schema_a.duration:.1f}s")
    print(f"Total segments: {len(schema_a.segments)}")
    
    # Collect emotion data
    emotions = []
    confidences = []
    emotion_segments = []
    
    for seg in schema_a.segments:
        if seg.emotion and seg.source == "whisper":
            emotions.append(seg.emotion)
            confidences.append(seg.emotion_confidence)
            emotion_segments.append(seg)
    
    if not emotions:
        print("No emotion data found in this file.")
        return
    
    # Calculate statistics
    emotion_counts = Counter(emotions)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    print(f"\nEmotion Statistics:")
    print(f"  Segments with emotions: {len(emotions)}")
    print(f"  Average confidence: {avg_confidence:.3f}")
    
    print(f"\nEmotion Distribution:")
    for emotion, count in emotion_counts.most_common():
        percentage = (count / len(emotions)) * 100
        print(f"  {emotion:10s}: {count:3d} ({percentage:5.1f}%)")
    
    # Show examples of each emotion
    print(f"\nExample segments by emotion:")
    for emotion in emotion_counts:
        examples = [seg for seg in emotion_segments if seg.emotion == emotion]
        if examples:
            seg = examples[0]
            print(f"\n{emotion.upper()} (confidence: {seg.emotion_confidence:.3f}):")
            print(f"  [{seg.start_time:6.1f}s] {seg.text[:60]}...")
    
    # Analyze emotion transitions
    if len(emotions) > 1:
        print(f"\nEmotion transitions:")
        transitions = Counter()
        for i in range(len(emotions) - 1):
            transition = f"{emotions[i]} -> {emotions[i+1]}"
            transitions[transition] += 1
        
        for transition, count in transitions.most_common(5):
            print(f"  {transition}: {count}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_emotions.py <schema_json_file> [<schema_json_file>...]")
        sys.exit(1)
    
    for path in sys.argv[1:]:
        if Path(path).exists():
            try:
                analyze_emotions(path)
            except Exception as e:
                print(f"Error analyzing {path}: {e}")
        else:
            print(f"File not found: {path}")


if __name__ == "__main__":
    main()