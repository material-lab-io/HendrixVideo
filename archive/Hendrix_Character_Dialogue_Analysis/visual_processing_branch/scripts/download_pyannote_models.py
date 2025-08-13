#!/usr/bin/env python3
"""
Download and cache Pyannote models for offline use
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / 'audio_processing_branch'))

def download_pyannote_models():
    """Download Pyannote models with HF token"""
    print("Downloading Pyannote models...")
    
    # Set the token
    token = os.environ.get('HF_TOKEN')
    if not token:
        print("ERROR: HF_TOKEN environment variable not set!")
        print("Please set your Hugging Face token: export HF_TOKEN=your_token")
        sys.exit(1)
    
    try:
        from pyannote.audio import Pipeline
        
        print(f"Using HF token: {token[:10]}...")
        
        # Download the models
        print("Downloading speaker-diarization-3.1 model...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token
        )
        
        print("Model downloaded successfully!")
        print(f"Pipeline loaded: {pipeline}")
        
        # Also download the segmentation model
        print("\nDownloading segmentation model...")
        from pyannote.audio import Model
        segmentation = Model.from_pretrained(
            "pyannote/segmentation-3.0", 
            use_auth_token=token
        )
        print("Segmentation model downloaded!")
        
        # Download embedding model
        print("\nDownloading embedding model...")
        embedding = Model.from_pretrained(
            "pyannote/wespeaker-voxceleb-resnet34-LM",
            use_auth_token=token
        )
        print("Embedding model downloaded!")
        
        print("\nAll models downloaded successfully!")
        print("Models are cached in: ~/.cache/torch/pyannote/")
        
        return True
        
    except Exception as e:
        print(f"Error downloading models: {e}")
        print("\nMake sure you have:")
        print("1. Accepted the terms at https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("2. Your token has read access")
        return False

if __name__ == "__main__":
    # Get token from environment
    if not os.environ.get('HF_TOKEN'):
        print("ERROR: HF_TOKEN environment variable not set!")
        print("Please set your Hugging Face token: export HF_TOKEN=your_token")
        sys.exit(1)
    download_pyannote_models()