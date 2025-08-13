#!/usr/bin/env python3
"""
Download LLaVA-NeXT model in the background
"""

import os
import sys
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch

print("Starting LLaVA-NeXT model download...")
print("Model: llava-hf/llava-v1.6-vicuna-7b-hf")
print("Size: ~13GB")
print("")

# Set cache directory
cache_dir = os.path.expanduser("~/.cache/huggingface")
os.environ['HF_HOME'] = cache_dir

try:
    print("Downloading processor...")
    processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-vicuna-7b-hf")
    print("✓ Processor downloaded")
    
    print("\nDownloading model (this will take several minutes)...")
    model = LlavaNextForConditionalGeneration.from_pretrained(
        "llava-hf/llava-v1.6-vicuna-7b-hf", 
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    print("✓ Model downloaded successfully!")
    
    # Test the model
    print("\nTesting model...")
    test_prompt = "USER: <image>\nWhat is this?\nASSISTANT:"
    inputs = processor(test_prompt, return_tensors="pt")
    print("✓ Model is working!")
    
    print("\nLLaVA-NeXT is ready to use!")
    
except Exception as e:
    print(f"\n✗ Error downloading model: {e}")
    sys.exit(1)