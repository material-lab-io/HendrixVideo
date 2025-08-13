#!/usr/bin/env python3
"""
Test wav2vec2 emotion recognition component
Tests on existing Schema A output
"""

import json
import logging
from pathlib import Path
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import SchemaA
from src.audio.emotion_processor import EmotionProcessor, EmotionConfig


def test_emotion_processor():
    """Test emotion processor on existing data"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Test file paths
    video_path = "test_video.mp4"
    audio_path = "test_audio.wav"  # Will be extracted
    schema_path = "output/schema_a_test_video.json"
    
    # Check if we have existing Schema A output
    if not Path(schema_path).exists():
        logger.error(f"Schema A file not found: {schema_path}")
        logger.info("Please run test_whisper_component.py first to generate Schema A")
        return
    
    # Load existing Schema A
    logger.info(f"Loading Schema A from: {schema_path}")
    with open(schema_path, 'r') as f:
        schema_data = json.load(f)
    
    schema_a = SchemaA.from_dict(schema_data)
    logger.info(f"Loaded {len(schema_a.segments)} segments")
    
    # Initialize emotion processor with development config
    config = EmotionConfig(
        model_name="superb/wav2vec2-large-superb-er",
        batch_size=4,  # Smaller batch for testing
        chunk_length_s=5.0,  # Shorter chunks for testing
    )
    
    logger.info("Initializing emotion processor...")
    start_time = time.time()
    processor = EmotionProcessor(config)
    init_time = time.time() - start_time
    logger.info(f"Processor initialized in {init_time:.2f} seconds")
    
    # Extract audio if not exists
    if not Path(audio_path).exists():
        logger.info("Extracting audio from video...")
        import subprocess
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            audio_path
        ]
        subprocess.run(cmd, check=True)
        logger.info(f"Audio extracted to: {audio_path}")
    
    # Process emotions
    logger.info("Processing emotions for segments...")
    start_time = time.time()
    enhanced_schema = processor.enhance_schema_a(schema_a, audio_path)
    process_time = time.time() - start_time
    
    # Save enhanced schema
    output_path = "output/schema_a_test_video_emotions.json"
    enhanced_schema.save_json(output_path)
    logger.info(f"Enhanced schema saved to: {output_path}")
    
    # Print results
    print("\n" + "="*60)
    print("EMOTION RECOGNITION RESULTS")
    print("="*60)
    
    print(f"\nProcessing time: {process_time:.2f} seconds")
    print(f"Average per segment: {process_time/len(schema_a.segments):.3f} seconds")
    
    # Show sample segments with emotions
    print("\nSample segments with emotions:")
    print("-" * 60)
    
    for i, segment in enumerate(enhanced_schema.segments[:5]):  # Show first 5
        if segment.source == "whisper":
            print(f"\nSegment {i}:")
            print(f"  Time: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
            print(f"  Text: {segment.text[:60]}...")
            print(f"  Emotion: {segment.emotion} (confidence: {segment.emotion_confidence:.3f})")
    
    # Emotion distribution
    print("\n" + "-"*60)
    print("Emotion Distribution:")
    emotion_counts = {}
    total_confidence = 0
    emotion_segments = 0
    
    for segment in enhanced_schema.segments:
        if segment.emotion and segment.source == "whisper":
            emotion_counts[segment.emotion] = emotion_counts.get(segment.emotion, 0) + 1
            total_confidence += segment.emotion_confidence
            emotion_segments += 1
    
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / emotion_segments * 100) if emotion_segments > 0 else 0
        print(f"  {emotion}: {count} segments ({percentage:.1f}%)")
    
    if emotion_segments > 0:
        avg_confidence = total_confidence / emotion_segments
        print(f"\nAverage confidence: {avg_confidence:.3f}")
    
    print("\n" + "="*60)
    print("Test completed successfully!")
    print("="*60)


if __name__ == "__main__":
    test_emotion_processor()