#!/usr/bin/env python3
"""
Test Whisper ASR with a longer YouTube video
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import logging

sys.path.insert(0, '.')

from src.audio.whisper_processor import WhisperProcessor, WhisperConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def download_youtube_video(url: str, output_name: str = "youtube_test") -> str:
    """Download video from YouTube
    
    Args:
        url: YouTube URL
        output_name: Output filename (without extension)
        
    Returns:
        Path to downloaded video
    """
    output_path = f"{output_name}.mp4"
    
    print(f"Downloading video from YouTube...")
    print(f"URL: {url}")
    
    # Use yt-dlp to download
    cmd = [
        'yt-dlp',
        '-f', 'best[height<=720]',  # Limit to 720p for faster download
        '-o', output_path,
        '--no-playlist',  # Only download single video
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Downloaded to: {output_path}")
        
        # Get video info
        info_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                    '-show_entries', 'stream=duration', '-of', 'json', output_path]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        duration = float(info['streams'][0]['duration'])
        print(f"✓ Video duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        raise


def analyze_transcription(schema_a):
    """Analyze and display transcription statistics"""
    
    print("\n=== Transcription Analysis ===")
    print(f"Video ID: {schema_a.video_id}")
    print(f"Total Duration: {schema_a.duration:.2f} seconds ({schema_a.duration/60:.2f} minutes)")
    print(f"Language Detected: {schema_a.metadata.get('language', 'unknown')}")
    print(f"Total Segments: {len(schema_a.segments)}")
    
    # Calculate statistics
    if schema_a.segments:
        # Segment lengths
        segment_lengths = [seg.end_time - seg.start_time for seg in schema_a.segments]
        avg_segment_length = sum(segment_lengths) / len(segment_lengths)
        
        # Word counts
        word_counts = [len(seg.text.split()) for seg in schema_a.segments]
        total_words = sum(word_counts)
        
        # Confidence scores
        confidences = [seg.confidence for seg in schema_a.segments]
        avg_confidence = sum(confidences) / len(confidences)
        
        print(f"\nSegment Statistics:")
        print(f"  Average segment length: {avg_segment_length:.2f} seconds")
        print(f"  Min segment length: {min(segment_lengths):.2f} seconds")
        print(f"  Max segment length: {max(segment_lengths):.2f} seconds")
        
        print(f"\nTranscription Statistics:")
        print(f"  Total words: {total_words}")
        print(f"  Average words per segment: {total_words/len(schema_a.segments):.1f}")
        print(f"  Words per minute: {(total_words / (schema_a.duration/60)):.1f}")
        
        print(f"\nConfidence Statistics:")
        print(f"  Average confidence: {avg_confidence:.2%}")
        print(f"  Min confidence: {min(confidences):.2%}")
        print(f"  Max confidence: {max(confidences):.2%}")
        
        # Show sample segments
        print(f"\n=== Sample Segments ===")
        
        # First 3 segments
        print("\nFirst 3 segments:")
        for i, seg in enumerate(schema_a.segments[:3]):
            print(f"\n[{i+1}] {seg.start_time:.2f}s - {seg.end_time:.2f}s (conf: {seg.confidence:.2%})")
            print(f"    \"{seg.text}\"")
        
        # Middle 3 segments
        mid_idx = len(schema_a.segments) // 2
        print(f"\nMiddle 3 segments (around {mid_idx}):")
        for i, seg in enumerate(schema_a.segments[mid_idx-1:mid_idx+2]):
            print(f"\n[{mid_idx+i}] {seg.start_time:.2f}s - {seg.end_time:.2f}s (conf: {seg.confidence:.2%})")
            print(f"    \"{seg.text}\"")
        
        # Last 3 segments
        print("\nLast 3 segments:")
        for i, seg in enumerate(schema_a.segments[-3:]):
            idx = len(schema_a.segments) - 3 + i + 1
            print(f"\n[{idx}] {seg.start_time:.2f}s - {seg.end_time:.2f}s (conf: {seg.confidence:.2%})")
            print(f"    \"{seg.text}\"")
        
        # Low confidence segments
        low_conf_segments = [seg for seg in schema_a.segments if seg.confidence < 0.5]
        if low_conf_segments:
            print(f"\n=== Low Confidence Segments ({len(low_conf_segments)}) ===")
            for seg in low_conf_segments[:5]:
                print(f"\n[{seg.start_time:.2f}s] (conf: {seg.confidence:.2%})")
                print(f"    \"{seg.text}\"")


def main():
    setup_logging()
    
    # YouTube video URLs to test (choose one)
    test_videos = {
        # TED-Ed educational video (4-5 minutes)
        "educational": "https://www.youtube.com/watch?v=RpkQEq75y18",
        # Tech explanation (5-6 minutes)
        "tech_talk": "https://www.youtube.com/watch?v=aircAruvnKk",
        # News/documentary style (3-4 minutes)
        "news": "https://www.youtube.com/watch?v=bBC-nXj3Ng4",
    }
    
    # Select video to test
    video_choice = "news"  # Change this to test different videos
    video_url = test_videos[video_choice]
    
    print(f"=== Testing Whisper ASR with YouTube Video ===")
    print(f"Video type: {video_choice}")
    
    # Download video
    try:
        video_path = download_youtube_video(video_url, f"youtube_{video_choice}")
    except Exception as e:
        print(f"Failed to download video: {e}")
        print("Make sure yt-dlp is installed: pip install yt-dlp")
        return
    
    # Test with both models
    models_to_test = [
        ("base", "Fast transcription"),
        ("large-v3", "High accuracy transcription")
    ]
    
    output_dir = Path("output/youtube_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for model_name, description in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing with {model_name} model - {description}")
        print(f"{'='*60}")
        
        # Create processor
        config = WhisperConfig(
            model_name=model_name,
            word_timestamps=True,
            language=None,  # Auto-detect
            temperature=0.0  # Deterministic
        )
        
        processor = WhisperProcessor(config)
        
        # Process video
        print(f"\nProcessing video with {model_name} model...")
        schema_a = processor.process_video(
            video_path, 
            video_id=f"{video_choice}_{model_name}"
        )
        
        # Save results
        output_path = output_dir / f"schema_a_{video_choice}_{model_name}.json"
        schema_a.save_json(str(output_path))
        print(f"✓ Saved transcription to: {output_path}")
        
        # Analyze results
        analyze_transcription(schema_a)
        
        # Compare processing time would be logged
        
    # Load and compare both results
    print(f"\n{'='*60}")
    print("=== Model Comparison ===")
    print(f"{'='*60}")
    
    base_path = output_dir / f"schema_a_{video_choice}_base.json"
    large_path = output_dir / f"schema_a_{video_choice}_large-v3.json"
    
    if base_path.exists() and large_path.exists():
        from src.schemas import SchemaA
        
        base_schema = SchemaA.load_json(str(base_path))
        large_schema = SchemaA.load_json(str(large_path))
        
        print(f"\nBase model segments: {len(base_schema.segments)}")
        print(f"Large model segments: {len(large_schema.segments)}")
        
        # Compare first segment
        if base_schema.segments and large_schema.segments:
            print(f"\nFirst segment comparison:")
            print(f"Base:  \"{base_schema.segments[0].text}\"")
            print(f"Large: \"{large_schema.segments[0].text}\"")
    
    print("\n✓ Testing complete!")


if __name__ == "__main__":
    main()