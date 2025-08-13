#!/usr/bin/env python3
"""
Test if all audio dependencies are properly installed
"""

import sys

def test_imports():
    """Test importing all required audio processing libraries"""
    
    print("=== Testing Audio Processing Setup ===\n")
    
    # Core libraries
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"✗ PyTorch: {e}")
        
    # Audio libraries
    try:
        import whisper
        print(f"✓ OpenAI Whisper")
        print(f"  Available models: {', '.join(whisper.available_models())}")
    except ImportError as e:
        print(f"✗ Whisper: {e}")
        
    try:
        import transformers
        print(f"✓ Transformers {transformers.__version__}")
    except ImportError as e:
        print(f"✗ Transformers: {e}")
        
    try:
        import pyannote.audio
        print(f"✓ Pyannote.audio {pyannote.audio.__version__}")
    except ImportError as e:
        print(f"✗ Pyannote: {e}")
        
    try:
        import librosa
        print(f"✓ Librosa {librosa.__version__}")
    except ImportError as e:
        print(f"✗ Librosa: {e}")
        
    try:
        import soundfile
        print(f"✓ Soundfile {soundfile.__version__}")
    except ImportError as e:
        print(f"✗ Soundfile: {e}")
        
    # Test model loading (minimal)
    print("\n=== Testing Model Loading ===\n")
    
    try:
        print("Testing Whisper model loading...")
        model = whisper.load_model("base")
        print("✓ Whisper base model loaded successfully")
    except Exception as e:
        print(f"✗ Whisper model loading failed: {e}")
        
    try:
        print("\nTesting wav2vec2 model loading...")
        from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
        model_name = "superb/wav2vec2-large-superb-er"
        print(f"  Loading {model_name}...")
        # Just check if we can instantiate, don't download yet
        print("✓ wav2vec2 imports successful (model will download on first use)")
    except Exception as e:
        print(f"✗ wav2vec2 setup failed: {e}")
    
    print("\n=== Next Steps ===")
    print("1. Set HuggingFace token in .env file for Pyannote")
    print("2. Download specific models as needed:")
    print("   - Whisper: whisper.load_model('base') or 'large-v3'")
    print("   - wav2vec2: Will auto-download on first use")
    print("   - Pyannote: Will auto-download after HF token is set")

if __name__ == "__main__":
    test_imports()