#!/usr/bin/env python3
"""
Debug script to test emotion processor
"""

import sys
import os
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio.emotion_processor import EmotionProcessor, EmotionConfig
from src.schemas import TranscriptionSegment

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_emotion_processor(audio_path):
    """Test emotion processor on an audio file"""
    print(f"Testing emotion processor on: {audio_path}")
    
    try:
        # Initialize processor
        config = EmotionConfig(
            model_name="superb/wav2vec2-large-superb-er",
            batch_size=1,
            aggregation_strategy="mean"
        )
        
        print("Initializing emotion processor...")
        processor = EmotionProcessor(config)
        print("✓ Emotion processor initialized successfully")
        
        # Create a test segment
        test_segment = TranscriptionSegment(
            segment_id="TEST_001",
            start_time=0.0,
            end_time=5.0,
            text="Test segment",
            confidence=1.0,
            source="whisper"
        )
        
        print("\nProcessing test segment (0-5 seconds)...")
        segments = processor.process_segments(str(audio_path), [test_segment])
        
        if segments[0].emotion:
            print(f"✓ Emotion detected: {segments[0].emotion} (confidence: {segments[0].emotion_confidence:.2f})")
        else:
            print("✗ No emotion detected")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_emotion_debug.py <audio_file>")
        sys.exit(1)
    
    test_emotion_processor(sys.argv[1])