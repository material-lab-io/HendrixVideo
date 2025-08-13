#!/usr/bin/env python3
"""Verify that all dependencies are correctly installed."""

import sys
import importlib
from typing import List, Tuple

def check_packages() -> Tuple[List[str], List[str]]:
    """Check if all required packages are installed."""
    required_packages = {
        # Core
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'PIL': 'pillow',
        
        # Deep learning
        'torch': 'torch',
        'torchvision': 'torchvision',
        'transformers': 'transformers',
        
        # Video processing
        'moviepy': 'moviepy',
        'ffmpeg': 'ffmpeg-python',
        
        # ML tools
        'scipy': 'scipy',
        'sklearn': 'scikit-learn',
        
        # LLM tools
        'accelerate': 'accelerate',
        'sentencepiece': 'sentencepiece',
        'google.protobuf': 'protobuf',
        
        # Utilities
        'yaml': 'pyyaml',
        'tqdm': 'tqdm',
        'pandas': 'pandas',
        'dotenv': 'python-dotenv',
        
        # Shot detection
        'transnetv2_pytorch': 'transnetv2-pytorch',
        
        # Dev tools
        'pytest': 'pytest',
        'black': 'black',
        'flake8': 'flake8',
    }
    
    installed = []
    missing = []
    
    for module, package in required_packages.items():
        try:
            importlib.import_module(module)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    return installed, missing

def check_cuda():
    """Check CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA is available")
            print(f"  - PyTorch version: {torch.__version__}")
            print(f"  - CUDA version: {torch.version.cuda}")
            print(f"  - Number of GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  - GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("✗ CUDA is not available (CPU-only mode)")
    except ImportError:
        print("✗ PyTorch not installed")

def check_ffmpeg():
    """Check FFmpeg installation."""
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        version_line = result.stdout.split('\n')[0]
        print(f"✓ FFmpeg is installed: {version_line}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg not found. Install with: sudo apt install ffmpeg")

def main():
    """Main verification function."""
    print("Verifying Hendrix Video Analysis installation...\n")
    
    # Check packages
    installed, missing = check_packages()
    
    print(f"Packages installed: {len(installed)}")
    if missing:
        print(f"\n✗ Missing packages ({len(missing)}):")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\nInstall missing packages with:")
        print(f"  pip install {' '.join(missing)}")
    else:
        print("✓ All required packages are installed")
    
    print("\nChecking CUDA support...")
    check_cuda()
    
    print("\nChecking FFmpeg...")
    check_ffmpeg()
    
    # Overall status
    print("\n" + "="*50)
    if not missing:
        print("✓ Installation verified successfully!")
        print("\nYou can now run the pipeline with:")
        print("  python src/main.py <video_file>")
    else:
        print("✗ Installation incomplete. Please install missing packages.")
        sys.exit(1)

if __name__ == "__main__":
    main()