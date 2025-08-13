#!/usr/bin/env python3
"""Analyze and summarize the pipeline results."""

import json
import os
from collections import Counter

def analyze_results():
    """Analyze the video analysis results."""
    
    # Load results
    with open('output/video_analysis_complete.json', 'r') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("HENDRIX VIDEO ANALYSIS RESULTS SUMMARY")
    print("=" * 60)
    
    # Video info
    print(f"\nVideo: {data['metadata']['filename']}")
    print(f"Duration: {data['metadata']['duration']:.2f} seconds ({data['metadata']['duration']/60:.1f} minutes)")
    print(f"Resolution: {data['metadata']['width']}x{data['metadata']['height']}")
    print(f"FPS: {data['metadata']['fps']}")
    print(f"Processing time: {data['processing_time']:.2f} seconds")
    
    # Shot detection results
    analysis = data['analysis']
    shots = analysis['shots']
    print(f"\n📊 SHOT DETECTION RESULTS:")
    print(f"Total shots detected: {len(shots)}")
    
    # Calculate shot statistics
    durations = [s['duration'] for s in shots]
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print(f"Average shot duration: {avg_duration:.2f} seconds")
    print(f"Shortest shot: {min_duration:.2f} seconds")
    print(f"Longest shot: {max_duration:.2f} seconds")
    
    # Show shot distribution
    print("\nShot duration distribution:")
    duration_ranges = {
        "0-2s": 0,
        "2-5s": 0,
        "5-10s": 0,
        "10-20s": 0,
        "20s+": 0
    }
    
    for d in durations:
        if d < 2:
            duration_ranges["0-2s"] += 1
        elif d < 5:
            duration_ranges["2-5s"] += 1
        elif d < 10:
            duration_ranges["5-10s"] += 1
        elif d < 20:
            duration_ranges["10-20s"] += 1
        else:
            duration_ranges["20s+"] += 1
    
    for range_name, count in duration_ranges.items():
        percentage = (count / len(shots)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {range_name:8} [{count:3d}]: {bar} {percentage:.1f}%")
    
    # Scene analysis results
    scenes = analysis['scenes']
    print(f"\n🎬 SCENE CONSTRUCTION RESULTS:")
    print(f"Total scenes: {len(scenes)}")
    
    # Sample some scenes with successful descriptions
    successful_scenes = [s for s in scenes if s.get('description') and 'Error' not in s['description']]
    if successful_scenes:
        print(f"\nSample scene descriptions:")
        for i, scene in enumerate(successful_scenes[:5]):
            print(f"\nScene {scene['scene_id']}:")
            print(f"  Shots: {scene['shot_ids']}")
            print(f"  Duration: {scene['end'] - scene['start']:.2f}s")
            print(f"  Description: {scene['description'][:100]}...")
    
    # Keyframes info
    keyframe_count = len([f for f in os.listdir('keyframes') if f.endswith('.jpg')])
    print(f"\n🖼️  KEYFRAMES:")
    print(f"Total keyframes extracted: {keyframe_count}")
    print(f"Location: keyframes/")
    
    # Show sample keyframes
    print("\nSample keyframes:")
    for i in range(1, min(6, keyframe_count + 1)):
        print(f"  - keyframes/shot_{i:04d}.jpg")
    
    print("\n" + "=" * 60)
    print("Analysis complete! Check the output/ directory for full results.")
    print("Keyframes are saved in the keyframes/ directory.")

if __name__ == "__main__":
    analyze_results()