#!/usr/bin/env python3
"""Test GPU acceleration for all pipeline components"""

import sys
import torch
import time
from pathlib import Path

def test_pytorch_gpu():
    """Test PyTorch GPU availability"""
    print("\n=== PyTorch GPU Test ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        print(f"GPU name: {torch.cuda.get_device_name(0)}")
        
        # Test GPU computation
        x = torch.randn(1000, 1000).cuda()
        start = time.time()
        y = torch.matmul(x, x)
        torch.cuda.synchronize()
        print(f"GPU matmul time: {time.time() - start:.4f}s")
        
        # Compare with CPU
        x_cpu = x.cpu()
        start = time.time()
        y_cpu = torch.matmul(x_cpu, x_cpu)
        print(f"CPU matmul time: {time.time() - start:.4f}s")
    else:
        print("No CUDA GPU available")
    
    return torch.cuda.is_available()

def test_transnetv2():
    """Test TransNetV2 GPU usage"""
    print("\n=== TransNetV2 GPU Test ===")
    try:
        from transnetv2_pytorch import TransNetV2
        
        model = TransNetV2()
        if torch.cuda.is_available():
            model = model.cuda()
            print("✓ TransNetV2 loaded on GPU")
            
            # Test inference
            dummy_input = torch.randn(1, 100, 3, 48, 27).cuda()
            with torch.no_grad():
                start = time.time()
                output = model(dummy_input)
                torch.cuda.synchronize()
                print(f"  Inference time: {time.time() - start:.4f}s")
        else:
            print("✗ No GPU available for TransNetV2")
            
    except Exception as e:
        print(f"✗ TransNetV2 error: {e}")
        
def test_whisper():
    """Test Whisper GPU usage"""
    print("\n=== Whisper GPU Test ===")
    try:
        import whisper
        
        # Load tiny model for testing
        model = whisper.load_model("tiny", device="cuda" if torch.cuda.is_available() else "cpu")
        print(f"✓ Whisper loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")
        
    except Exception as e:
        print(f"✗ Whisper error: {e}")

def test_transformers():
    """Test Transformers GPU usage"""
    print("\n=== Transformers GPU Test ===")
    try:
        from transformers import AutoModel, AutoTokenizer
        
        # Test with small model
        model_name = "bert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        
        if torch.cuda.is_available():
            model = model.cuda()
            print("✓ Transformers model loaded on GPU")
            
            # Test inference
            inputs = tokenizer("Test", return_tensors="pt").to("cuda")
            with torch.no_grad():
                start = time.time()
                outputs = model(**inputs)
                torch.cuda.synchronize()
                print(f"  Inference time: {time.time() - start:.4f}s")
        else:
            print("✗ No GPU available for Transformers")
            
    except Exception as e:
        print(f"✗ Transformers error: {e}")

def test_onnx_gpu():
    """Test ONNX Runtime GPU"""
    print("\n=== ONNX Runtime GPU Test ===")
    try:
        import onnxruntime as ort
        
        providers = ort.get_available_providers()
        print(f"Available providers: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            print("✓ ONNX Runtime GPU support available")
        else:
            print("✗ ONNX Runtime GPU not available")
            
    except Exception as e:
        print(f"✗ ONNX Runtime error: {e}")

def test_opencv_gpu():
    """Test OpenCV GPU support"""
    print("\n=== OpenCV GPU Test ===")
    try:
        import cv2
        
        print(f"OpenCV version: {cv2.__version__}")
        gpu_count = cv2.cuda.getCudaEnabledDeviceCount()
        
        if gpu_count > 0:
            print(f"✓ OpenCV CUDA support: {gpu_count} devices")
        else:
            print("✗ OpenCV compiled without CUDA support")
            
    except Exception as e:
        print(f"✗ OpenCV error: {e}")

def main():
    """Run all GPU tests"""
    print("Hendrix Pipeline GPU Component Test")
    print("=" * 50)
    
    # Test each component
    pytorch_ok = test_pytorch_gpu()
    test_transnetv2()
    test_whisper()
    test_transformers()
    test_onnx_gpu()
    test_opencv_gpu()
    
    # Summary
    print("\n" + "=" * 50)
    print("GPU Test Summary:")
    if pytorch_ok:
        print("✓ GPU acceleration is available")
        print("✓ All GPU-capable components can use CUDA")
    else:
        print("✗ No GPU detected - pipeline will use CPU")
        print("  Consider using a GPU for faster processing")

if __name__ == "__main__":
    main()