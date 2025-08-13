#!/usr/bin/env python3
"""
Test Complete Audio Processing Pipeline
Simple script to test all components are working together
"""

import os
import sys
from pathlib import Path
import subprocess
import json


def check_requirements():
    """Check all requirements are met"""
    print("Checking requirements...")
    
    # Check HF_TOKEN
    if not os.environ.get("HF_TOKEN"):
        print("⚠️  HF_TOKEN not set - loading from .env")
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("HF_TOKEN="):
                        token = line.strip().split("=", 1)[1]
                        os.environ["HF_TOKEN"] = token
                        print("✓ HF_TOKEN loaded from .env")
                        break
    else:
        print("✓ HF_TOKEN is set")
    
    # Check test video exists
    test_videos = [
        "test_video.mp4",
        "youtube_educational.mp4",
        "youtube_news.mp4"
    ]
    
    available_videos = []
    for video in test_videos:
        if Path(video).exists():
            available_videos.append(video)
    
    if not available_videos:
        print("✗ No test videos found")
        print("  Please ensure one of these exists:")
        for video in test_videos:
            print(f"    - {video}")
        return None
    
    print(f"✓ Found test videos: {', '.join(available_videos)}")
    return available_videos[0]  # Return first available


def run_pipeline_test(video_path):
    """Run the complete pipeline"""
    print(f"\nRunning complete pipeline on: {video_path}")
    print("-" * 60)
    
    # Run the pipeline
    cmd = [
        sys.executable,
        "complete_audio_pipeline.py",
        video_path,
        "--whisper-model", "base",  # Use base for faster testing
        "--min-speakers", "1",
        "--max-speakers", "3",
        "-v"  # Verbose output
    ]
    
    # Set environment for subprocess
    env = os.environ.copy()
    
    result = subprocess.run(cmd, env=env)
    
    return result.returncode == 0


def check_outputs():
    """Check and display pipeline outputs"""
    print("\nChecking outputs...")
    
    # Find latest output directory
    pipeline_dir = Path("output/pipeline")
    if not pipeline_dir.exists():
        print("✗ No pipeline output directory found")
        return False
    
    # Get most recent output
    output_dirs = sorted(
        [d for d in pipeline_dir.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not output_dirs:
        print("✗ No output directories found")
        return False
    
    latest_output = output_dirs[0]
    print(f"\n✓ Latest output: {latest_output}")
    
    # Check for expected files
    expected_files = {
        "schemas/schema_a_transcription.json": "Transcription",
        "schemas/schema_a_with_emotions.json": "Transcription + Emotions",
        "schemas/schema_b_speakers.json": "Speaker Diarization",
        "reports/pipeline_summary.json": "Pipeline Summary",
        "reports/audio_analysis_report.md": "Analysis Report",
        "logs/pipeline.log": "Processing Log"
    }
    
    print("\nOutput files:")
    all_found = True
    for file_path, description in expected_files.items():
        full_path = latest_output / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✓ {description}: {file_path} ({size} bytes)")
        else:
            print(f"  ✗ {description}: {file_path} (not found)")
            all_found = False
    
    # Display summary from pipeline report
    summary_path = latest_output / "reports/pipeline_summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
        
        print(f"\nPipeline Summary:")
        print(f"  Total time: {summary['total_time']:.1f}s")
        print(f"  Components:")
        for component, timing in summary['timings'].items():
            print(f"    - {component}: {timing:.1f}s")
        
        if summary['errors']:
            print(f"  Errors: {len(summary['errors'])}")
            for error in summary['errors']:
                print(f"    - {error}")
    
    return all_found


def main():
    print("="*60)
    print("COMPLETE AUDIO PIPELINE TEST")
    print("="*60)
    
    # Check requirements
    video_path = check_requirements()
    if not video_path:
        sys.exit(1)
    
    # Run pipeline
    success = run_pipeline_test(video_path)
    
    if success:
        print("\n✓ Pipeline completed successfully!")
        
        # Check outputs
        outputs_ok = check_outputs()
        
        if outputs_ok:
            print("\n✓ All expected outputs generated!")
            print("\nTo view the results, check the latest directory in:")
            print("  output/pipeline/")
        else:
            print("\n⚠️  Some outputs missing")
    else:
        print("\n✗ Pipeline failed!")
        print("Check the logs for details")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()