#!/usr/bin/env python3
"""
Test Pyannote speaker diarization component
Generates Schema B with speaker segments
"""

import os
import logging
from pathlib import Path
import time
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.schemas import SchemaB
from src.audio.diarization_processor import DiarizationProcessor, DiarizationConfig


def test_diarization():
    """Test speaker diarization on sample video"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check HF_TOKEN
    if not os.environ.get("HF_TOKEN"):
        logger.error("HF_TOKEN environment variable not set!")
        logger.error("Please set your HuggingFace token: export HF_TOKEN=your_token")
        logger.error("Make sure you've accepted terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
        sys.exit(1)
    
    # Test file
    video_path = "test_video.mp4"
    
    if not Path(video_path).exists():
        logger.error(f"Test video not found: {video_path}")
        logger.info("Please ensure test_video.mp4 exists in the current directory")
        sys.exit(1)
    
    # Initialize processor
    config = DiarizationConfig(
        model_name="pyannote/speaker-diarization-3.1",
        min_speakers=1,  # At least 1 speaker
        max_speakers=5,  # At most 5 speakers
        min_duration=0.5  # Minimum segment duration
    )
    
    logger.info("Initializing diarization processor...")
    start_time = time.time()
    
    try:
        processor = DiarizationProcessor(config)
        init_time = time.time() - start_time
        logger.info(f"Processor initialized in {init_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}")
        sys.exit(1)
    
    # Process video
    logger.info(f"Processing video: {video_path}")
    start_time = time.time()
    
    try:
        schema_b = processor.process_video(video_path)
        process_time = time.time() - start_time
        logger.info(f"Processing completed in {process_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Failed to process video: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Merge overlapping segments
    logger.info("Merging overlapping segments...")
    schema_b = processor.merge_overlapping_segments(schema_b, overlap_threshold=0.5)
    
    # Save Schema B
    output_path = "output/schema_b_test_video.json"
    Path("output").mkdir(exist_ok=True)
    schema_b.save_json(output_path)
    logger.info(f"Schema B saved to: {output_path}")
    
    # Print results
    print("\n" + "="*60)
    print("SPEAKER DIARIZATION RESULTS")
    print("="*60)
    
    print(f"\nVideo: {schema_b.video_id}")
    print(f"Duration: {schema_b.duration:.2f} seconds")
    print(f"Number of speakers: {schema_b.num_speakers}")
    print(f"Total segments: {len(schema_b.segments)}")
    
    # Get speaker statistics
    stats = schema_b.get_speaker_stats()
    
    print("\nSpeaker Statistics:")
    print("-" * 40)
    for speaker_id, speaker_stats in sorted(stats.items()):
        print(f"\n{speaker_id}:")
        print(f"  Speaking time: {speaker_stats['total_time']:.2f}s")
        print(f"  Percentage: {speaker_stats['percentage']:.1f}%")
        print(f"  Number of segments: {speaker_stats['num_segments']}")
    
    # Show sample segments
    print("\n" + "-" * 40)
    print("Sample Speaker Segments:")
    print("-" * 40)
    
    for i, segment in enumerate(schema_b.segments[:10]):  # Show first 10
        print(
            f"{i+1:2d}. [{segment.start_time:6.2f}s - {segment.end_time:6.2f}s] "
            f"{segment.speaker_id} (duration: {segment.end_time - segment.start_time:.2f}s)"
        )
    
    if len(schema_b.segments) > 10:
        print(f"... and {len(schema_b.segments) - 10} more segments")
    
    print("\n" + "="*60)
    print("Test completed successfully!")
    print("="*60)


if __name__ == "__main__":
    test_diarization()