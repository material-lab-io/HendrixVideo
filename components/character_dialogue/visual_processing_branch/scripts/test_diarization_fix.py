#!/usr/bin/env python3
"""Test diarization with explicit speaker parameters"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'audio_processing_branch'))

# Get HF token from environment
if not os.environ.get('HF_TOKEN'):
    print("ERROR: HF_TOKEN environment variable not set!")
    print("Please set your Hugging Face token: export HF_TOKEN=your_token")
    sys.exit(1)
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import tempfile
import subprocess
from pyannote.audio import Pipeline

def test_diarization():
    """Test diarization with different parameters"""
    print("Testing diarization with explicit parameters...")
    
    video_path = "/dev-work/audio_analysis/visual_processing_branch/test_videos/interview_video.mp4"
    
    # Extract audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        tmp_audio_path = tmp_audio.name
    
    print(f"Extracting audio to: {tmp_audio_path}")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        "-y", tmp_audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Load pipeline
    print("Loading Pyannote pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=os.environ['HF_TOKEN']
    )
    
    # Test 1: Auto-detect speakers
    print("\nTest 1: Auto-detect speakers")
    diarization = pipeline(tmp_audio_path)
    speakers = set()
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speakers.add(speaker)
    print(f"Auto-detected speakers: {len(speakers)} - {speakers}")
    
    # Test 2: Force 2 speakers
    print("\nTest 2: Force exactly 2 speakers")
    diarization = pipeline(tmp_audio_path, num_speakers=2)
    speakers = set()
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speakers.add(speaker)
    print(f"Forced 2 speakers: {len(speakers)} - {speakers}")
    
    # Test 3: Min/max speakers
    print("\nTest 3: Min 2, Max 4 speakers")
    diarization = pipeline(tmp_audio_path, min_speakers=2, max_speakers=4)
    speakers = set()
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speakers.add(speaker)
    print(f"Min/max speakers: {len(speakers)} - {speakers}")
    
    # Show some segments
    print("\nFirst 10 segments:")
    count = 0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"  {turn.start:.1f}s - {turn.end:.1f}s: {speaker}")
        count += 1
        if count >= 10:
            break
    
    # Clean up
    os.unlink(tmp_audio_path)
    
    print("\nDiarization test complete!")

if __name__ == "__main__":
    test_diarization()