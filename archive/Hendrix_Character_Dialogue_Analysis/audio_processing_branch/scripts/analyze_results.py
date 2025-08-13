#!/usr/bin/env python3
"""
Analyze and display Whisper transcription results
"""

import json
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import SchemaA


def display_transcription_results(json_path: str):
    """Display formatted transcription results"""
    
    print(f"\n=== Analyzing: {Path(json_path).name} ===\n")
    
    # Load schema
    schema_a = SchemaA.load_json(json_path)
    
    # Basic info
    print(f"Video ID: {schema_a.video_id}")
    print(f"Duration: {schema_a.duration:.1f} seconds ({schema_a.duration/60:.1f} minutes)")
    print(f"Language: {schema_a.metadata.get('language', 'unknown')}")
    print(f"Model: {schema_a.metadata.get('whisper_model', 'unknown')}")
    print(f"Total Segments: {len(schema_a.segments)}")
    
    # Statistics
    if schema_a.segments:
        confidences = [seg.confidence for seg in schema_a.segments]
        word_counts = [len(seg.text.split()) for seg in schema_a.segments]
        
        print(f"\nStatistics:")
        print(f"  Average confidence: {sum(confidences)/len(confidences):.1%}")
        print(f"  Total words: {sum(word_counts)}")
        print(f"  Words per minute: {sum(word_counts)/(schema_a.duration/60):.0f}")
        
        # Show full transcription
        print(f"\n=== Full Transcription ===\n")
        for i, seg in enumerate(schema_a.segments):
            print(f"[{seg.start_time:6.2f}s - {seg.end_time:6.2f}s] {seg.text}")
            if i < len(schema_a.segments) - 1:
                # Show gap between segments if > 0.5s
                gap = schema_a.segments[i+1].start_time - seg.end_time
                if gap > 0.5:
                    print(f"{'':>25} [silence: {gap:.1f}s]")
        
        # Word frequency analysis
        print(f"\n=== Word Frequency (Top 20) ===")
        from collections import Counter
        all_words = ' '.join(seg.text.lower() for seg in schema_a.segments).split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                      'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                      'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'he',
                      'she', 'it', 'we', 'they', 'them', 'their', 'this', 'that', 'these',
                      'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        
        filtered_words = [w for w in all_words if w not in stop_words and len(w) > 2]
        word_freq = Counter(filtered_words)
        
        for word, count in word_freq.most_common(20):
            print(f"  {word}: {count}")


def main():
    # Find all schema_a files in output
    output_dir = Path("output/youtube_test")
    if not output_dir.exists():
        print("No output directory found. Run test_whisper_youtube.py first.")
        return
    
    schema_files = sorted(output_dir.glob("schema_a_*.json"))
    
    if not schema_files:
        print("No transcription files found.")
        return
    
    print(f"Found {len(schema_files)} transcription files")
    
    # Display each one
    for schema_file in schema_files:
        display_transcription_results(str(schema_file))
        print("\n" + "="*80)


if __name__ == "__main__":
    main()