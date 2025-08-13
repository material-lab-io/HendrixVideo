#!/usr/bin/env python3
"""Test GPU usage for different models"""

import torch
import subprocess
import time
import threading

def monitor_gpu():
    """Monitor GPU usage in a separate thread"""
    for i in range(30):
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        print(f"[{i}s] {result.stdout.strip()}")
        time.sleep(1)

print("Testing GPU usage for Hendrix models...")
print(f"PyTorch CUDA available: {torch.cuda.is_available()}")
print(f"CUDA devices: {torch.cuda.device_count()}")
print()

# Start GPU monitoring
monitor_thread = threading.Thread(target=monitor_gpu)
monitor_thread.daemon = True
monitor_thread.start()

# Test Whisper
print("Loading Whisper...")
import whisper
model = whisper.load_model("tiny")
print(f"Whisper device: {model.device}")

# Test inference
print("\nRunning Whisper inference...")
audio = whisper.pad_or_trim(torch.randn(16000 * 30))  # 30 seconds of random audio
result = model.transcribe(audio.numpy(), language="en")
print(f"Transcription done. Length: {len(result['text'])}")

# Test InsightFace
print("\nLoading InsightFace...")
try:
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(allowed_modules=['detection', 'recognition'], providers=['CUDAExecutionProvider'])
    app.prepare(ctx_id=0)
    print("InsightFace loaded on GPU")
except Exception as e:
    print(f"InsightFace error: {e}")

# Keep monitoring for a bit
time.sleep(5)
print("\nTest complete.")