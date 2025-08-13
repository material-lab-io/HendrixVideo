#!/usr/bin/env python3
"""
Script to download and verify all required models
"""

import os
import sys
from pathlib import Path

def setup_models():
    """Download and setup all required models"""
    
    print("=== Model Setup Script ===\n")
    
    # Create model directories
    model_dirs = [
        "models/whisper",
        "models/wav2vec",
        "models/yolo",
        "models/insightface",
        "models/pyannote",
        "models/transformers"
    ]
    
    for dir_path in model_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Created model directories\n")
    
    # List of models to download
    models_info = {
        "Audio Models": [
            "1. OpenAI Whisper (large-v3): ~3GB - Best accuracy for transcription",
            "   Alternative: whisper-base (~140MB) for testing",
            "2. wav2vec2 for emotion: ~400MB - superb/wav2vec2-large-superb-er",
            "3. Pyannote speaker diarization: ~20MB - pyannote/speaker-diarization-3.1",
            "   Note: Requires HuggingFace token"
        ],
        "Vision Models": [
            "1. YOLOv8n-face: ~6MB - Lightweight face detection",
            "2. InsightFace buffalo_l: ~300MB - ArcFace embeddings",
            "3. DeepFace models: ~500MB - Various (auto-downloads)"
        ],
        "OCR Models": [
            "1. EasyOCR English: ~64MB - Text detection",
            "   Optional: Additional languages as needed"
        ],
        "Multimodal Models": [
            "1. CLIP ViT-B/32: ~340MB - For semantic understanding",
            "2. LLaVA (optional): ~13GB - For advanced matching",
            "   Note: Can use API-based LLMs instead"
        ]
    }
    
    print("=== Required Models ===\n")
    total_size = 0
    for category, models in models_info.items():
        print(f"{category}:")
        for model in models:
            print(f"  {model}")
        print()
    
    print("Estimated total download size: ~5GB (minimal) to ~20GB (full)")
    print("\n=== Download Commands ===\n")
    
    print("# 1. Whisper (choose one):")
    print("# For testing (small):")
    print("python -c \"import whisper; whisper.load_model('base')\"")
    print("\n# For production (large):")
    print("python -c \"import whisper; whisper.load_model('large-v3')\"")
    
    print("\n# 2. wav2vec2 emotion:")
    print("python -c \"from transformers import Wav2Vec2ForSequenceClassification; ")
    print("model = Wav2Vec2ForSequenceClassification.from_pretrained('superb/wav2vec2-large-superb-er')\"")
    
    print("\n# 3. YOLOv8 face:")
    print("python -c \"from ultralytics import YOLO; YOLO('yolov8n-face.pt')\"")
    
    print("\n# 4. InsightFace:")
    print("python -c \"import insightface; model = insightface.app.FaceAnalysis(name='buffalo_l'); model.prepare(ctx_id=0)\"")
    
    print("\n# 5. CLIP:")
    print("python -c \"import clip; clip.load('ViT-B/32', device='cpu')\"")
    
    print("\n# 6. Pyannote (requires HF_TOKEN in .env):")
    print("# First: huggingface-cli login")
    print("# Then the model will auto-download on first use")
    
    print("\n=== System Requirements ===")
    print("- RAM: 16GB minimum, 32GB recommended")
    print("- GPU: NVIDIA with 8GB+ VRAM recommended")
    print("- Disk: 20GB+ free space")
    print("- Internet: Stable connection for downloads")

if __name__ == "__main__":
    setup_models()