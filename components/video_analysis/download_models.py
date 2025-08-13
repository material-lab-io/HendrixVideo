#!/usr/bin/env python3
"""
Download and cache models for Hendrix Video Analysis Pipeline
"""
import os
import sys

# Set cache directories
os.environ['HF_HOME'] = '/dev-work/Hendrix_Video_Analysis/cache/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/dev-work/Hendrix_Video_Analysis/cache/transformers'
os.environ['TORCH_HOME'] = '/dev-work/Hendrix_Video_Analysis/cache/torch'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration
from transnetv2_pytorch import TransNetV2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_llava_model():
    """Download and cache LLaVA model"""
    model_name = "llava-hf/llava-1.5-7b-hf"
    
    logger.info(f"Downloading LLaVA model: {model_name}")
    logger.info(f"Cache directory: {os.environ['HF_HOME']}")
    
    try:
        # Download processor
        logger.info("Downloading processor...")
        processor = AutoProcessor.from_pretrained(model_name)
        logger.info("Processor downloaded successfully")
        
        # Download model with float16 precision
        logger.info("Downloading model (this may take a while)...")
        model = LlavaForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            device_map="auto"
        )
        logger.info("Model downloaded successfully")
        
        # Test model loading
        logger.info("Testing model...")
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            logger.info("CUDA not available, model will run on CPU")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to download LLaVA model: {e}")
        return False

def download_transnetv2_model():
    """Download and cache TransNetV2 model"""
    logger.info("Downloading TransNetV2 model weights...")
    
    try:
        # Initialize model (this will download weights if needed)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = TransNetV2(device=device)
        logger.info("TransNetV2 model downloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download TransNetV2 model: {e}")
        return False

def main():
    """Main function to download all models"""
    print("=" * 60)
    print("Hendrix Video Analysis Pipeline - Model Downloader")
    print("=" * 60)
    
    # Check disk space
    import shutil
    path = "/dev-work/Hendrix_Video_Analysis/cache"
    stat = shutil.disk_usage(path)
    free_gb = stat.free / (1024**3)
    print(f"\nAvailable disk space: {free_gb:.1f} GB")
    
    if free_gb < 20:
        print("WARNING: Less than 20GB free space. Model download may fail.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\nThis will download:")
    print("1. LLaVA-1.5-7B model (~13GB)")
    print("2. TransNetV2 model (~100MB)")
    print("\nModels will be cached in: /dev-work/Hendrix_Video_Analysis/cache/")
    
    response = input("\nProceed with download? (y/n): ")
    if response.lower() != 'y':
        print("Download cancelled.")
        return
    
    # Download models
    print("\n" + "="*60)
    success = True
    
    # Download TransNetV2
    print("\n[1/2] Downloading TransNetV2...")
    if not download_transnetv2_model():
        success = False
    
    # Download LLaVA
    print("\n[2/2] Downloading LLaVA...")
    if not download_llava_model():
        success = False
    
    print("\n" + "="*60)
    if success:
        print("✓ All models downloaded successfully!")
        print("\nYou can now run the pipeline with:")
        print("  python src/main.py <video_file>")
    else:
        print("✗ Some models failed to download. Please check the errors above.")

if __name__ == "__main__":
    main()