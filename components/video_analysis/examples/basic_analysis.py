#!/usr/bin/env python3
"""
Basic video analysis example using Hendrix Video Analysis Pipeline.

Usage:
    python examples/basic_analysis.py path/to/video.mp4
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import VideoAnalysisPipeline


def main():
    parser = argparse.ArgumentParser(description="Basic video analysis example")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--config", default="config.yaml", help="Configuration file")
    args = parser.parse_args()
    
    # Check if video exists
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    print(f"Analyzing video: {args.video}")
    print("=" * 50)
    
    try:
        # Initialize pipeline
        pipeline = VideoAnalysisPipeline(args.config)
        
        # Analyze video
        results = pipeline.analyze_video(
            args.video,
            output_dir=args.output_dir
        )
        
        # Display results summary
        print("\nAnalysis Complete!")
        print("=" * 50)
        
        # Shot detection results
        shots = results.get('shots', [])
        print(f"\nShot Detection Results:")
        print(f"  Total shots detected: {len(shots)}")
        if shots:
            print(f"  Video duration: {shots[-1].end:.2f} seconds")
            print(f"  Average shot duration: {sum(s.duration for s in shots) / len(shots):.2f} seconds")
            print(f"  Shortest shot: {min(s.duration for s in shots):.2f} seconds")
            print(f"  Longest shot: {max(s.duration for s in shots):.2f} seconds")
        
        # Scene construction results
        scenes = results.get('scenes', [])
        print(f"\nScene Construction Results:")
        print(f"  Total scenes: {len(scenes)}")
        
        # Display first few scenes
        print("\n  First 5 scenes:")
        for i, scene in enumerate(scenes[:5]):
            print(f"    Scene {scene.scene_id}: {scene.summary}")
            print(f"      Shots: {scene.contained_shots}")
            print(f"      Duration: {scene.start_time:.2f}s - {scene.end_time:.2f}s")
            print()
        
        # Output location
        print(f"\nDetailed results saved to: {args.output_dir}/")
        print(f"  - Shots: {args.output_dir}/shots.json")
        print(f"  - Scenes: {args.output_dir}/scenes.json")
        print(f"  - Keyframes: {args.output_dir}/keyframes/")
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()