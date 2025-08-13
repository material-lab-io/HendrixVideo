#!/usr/bin/env python3
"""
Test Whisper ASR component with a sample video
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.whisper_processor import WhisperProcessor, WhisperConfig
import json


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def download_test_video():
    """Download a short test video"""
    import subprocess
    
    # Use a short clip for testing
    test_url = "https://www.w3schools.com/html/mov_bbb.mp4"
    output_path = "test_video.mp4"
    
    if not os.path.exists(output_path):
        print(f"Downloading test video from {test_url}...")
        subprocess.run(['wget', '-q', test_url, '-O', output_path], check=True)
        print(f"Downloaded to {output_path}")
    else:
        print(f"Test video already exists: {output_path}")
    
    return output_path


def test_whisper_processor():
    """Test the Whisper processor"""
    setup_logging()
    
    # Download test video
    video_path = download_test_video()
    
    print("\n=== Testing Whisper Processor ===\n")
    
    # Create processor with base model for faster testing
    config = WhisperConfig(
        model_name="base",  # Use base for testing
        word_timestamps=True
    )
    
    processor = WhisperProcessor(config)
    
    # Process video
    print(f"Processing video: {video_path}")
    schema_a = processor.process_video(video_path, video_id="test_video")
    
    # Display results
    print(f"\n=== Transcription Results ===")
    print(f"Video ID: {schema_a.video_id}")
    print(f"Duration: {schema_a.duration:.2f} seconds")
    print(f"Language: {schema_a.metadata.get('language', 'unknown')}")
    print(f"Total segments: {len(schema_a.segments)}")
    
    print(f"\n=== Transcription Segments ===")
    for segment in schema_a.segments[:5]:  # Show first 5 segments
        print(f"\n[{segment.start_time:.2f}s - {segment.end_time:.2f}s] (conf: {segment.confidence:.2f})")
        print(f"  {segment.text}")
    
    if len(schema_a.segments) > 5:
        print(f"\n... and {len(schema_a.segments) - 5} more segments")
    
    # Save to JSON
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "schema_a_test.json"
    schema_a.save_json(str(output_path))
    print(f"\n✓ Schema A saved to: {output_path}")
    
    # Show JSON structure
    print(f"\n=== JSON Structure (first segment) ===")
    print(json.dumps(schema_a.segments[0].to_dict(), indent=2))
    
    # Test production model
    print("\n=== Testing with Production Model (large-v3) ===")
    prod_config = WhisperConfig(
        model_name="large-v3",
        word_timestamps=True
    )
    
    prod_processor = WhisperProcessor(prod_config)
    
    # Process first 10 seconds only for speed
    print("Processing with large-v3 model...")
    prod_schema = prod_processor.process_video(video_path, video_id="test_video_prod")
    
    print(f"\nProduction model results:")
    print(f"Language detected: {prod_schema.metadata.get('language', 'unknown')}")
    print(f"Total segments: {len(prod_schema.segments)}")
    
    # Compare first segment
    if prod_schema.segments:
        print(f"\nFirst segment (production):")
        print(f"[{prod_schema.segments[0].start_time:.2f}s - {prod_schema.segments[0].end_time:.2f}s]")
        print(f"  {prod_schema.segments[0].text}")


if __name__ == "__main__":
    test_whisper_processor()