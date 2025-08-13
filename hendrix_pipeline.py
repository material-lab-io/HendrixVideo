#!/usr/bin/env python3
"""
Hendrix Pipeline - Main Entry Point
Unified pipeline for video analysis, character detection, and caption generation
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from components.config_manager import ConfigManager, list_all_models


def main():
    parser = argparse.ArgumentParser(
        description="Hendrix Video Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m hendrix_pipeline --video input.mp4
  
  # Use fast profile
  python -m hendrix_pipeline --video input.mp4 --profile fast
  
  # Use specific models
  python -m hendrix_pipeline --video input.mp4 --vlm-model llava_13b --whisper-model large
  
  # List available models
  python -m hendrix_pipeline --list-models
  
  # Verify installation
  python -m hendrix_pipeline --verify
        """
    )
    
    # Input options
    parser.add_argument("--video", type=str, help="Path to input video file")
    
    # Configuration options
    parser.add_argument("--config", type=str, default="configs/base_config.yaml",
                       help="Path to configuration file")
    parser.add_argument("--profile", type=str, choices=["fast", "balanced", "quality", "test"],
                       default="balanced", help="Configuration profile to use")
    
    # Model options
    parser.add_argument("--vlm-model", type=str, help="Vision-language model to use")
    parser.add_argument("--whisper-model", type=str, help="Whisper model size")
    parser.add_argument("--model-preset", type=str, help="Use a model preset")
    
    # Output options
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--output-formats", type=str, nargs="+",
                       default=["json", "srt", "vtt", "html"],
                       help="Output formats to generate")
    
    # Component options
    parser.add_argument("--components", type=str, nargs="+",
                       default=["video", "audio", "caption"],
                       help="Components to run")
    parser.add_argument("--skip-component", type=str, nargs="+",
                       help="Components to skip")
    
    # Performance options
    parser.add_argument("--device", type=str, default="auto",
                       help="Device to use (cuda:0, cuda:1, cpu, auto)")
    parser.add_argument("--quantize", type=str, choices=["8bit", "4bit", "none"],
                       default="none", help="Model quantization")
    
    # Utility options
    parser.add_argument("--list-models", action="store_true",
                       help="List all available models")
    parser.add_argument("--verify", action="store_true",
                       help="Verify installation")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without executing")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--log-level", type=str, default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Handle utility commands
    if args.list_models:
        list_all_models(args.config)
        return 0
    
    if args.verify:
        return verify_installation(args.config)
    
    # Check video input
    if not args.video:
        parser.print_help()
        return 1
    
    # Load configuration
    config = ConfigManager(args.config, profile=args.profile)
    
    # Apply model overrides
    if args.vlm_model:
        config.set_active_model(args.vlm_model)
    if args.whisper_model:
        config.set("audio_models.whisper.model", args.whisper_model)
    if args.quantize != "none":
        active_model = config.get("active_model")
        config.set(f"models.{active_model}.device_config.load_in_{args.quantize}", True)
    
    # Set device
    if args.device != "auto":
        config.set("pipeline.device", args.device)
    
    # Handle component selection
    components = set(args.components)
    if args.skip_component:
        components -= set(args.skip_component)
    
    # Set output formats
    config.set("output.formats", args.output_formats)
    
    # Dry run
    if args.dry_run:
        print_dry_run_info(args, config, components)
        return 0
    
    # Run the pipeline
    try:
        from components.pipeline import Pipeline
        
        pipeline = Pipeline(config)
        results = pipeline.process_video(
            args.video,
            output_dir=args.output_dir,
            components=list(components),
            verbose=args.verbose
        )
        
        print(f"\nPipeline completed successfully!")
        print(f"Results saved to: {results['output_dir']}")
        
        return 0
        
    except Exception as e:
        print(f"\nPipeline failed with error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def verify_installation(config_path):
    """Verify that the pipeline is correctly installed"""
    print("Verifying Hendrix Pipeline installation...")
    
    issues = []
    
    # Check Python version
    import sys
    if sys.version_info < (3, 8):
        issues.append(f"Python {sys.version_info.major}.{sys.version_info.minor} detected. Python 3.8+ required.")
    
    # Check required packages
    required_packages = [
        ("torch", "torch"),
        ("torchvision", "torchvision"), 
        ("transformers", "transformers"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("pyyaml", "yaml"),
        ("tqdm", "tqdm")
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            issues.append(f"Missing package: {package_name}")
            print(f"  ✗ {package_name}")
    
    # Check CUDA availability
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ CUDA available (Device: {torch.cuda.get_device_name(0)})")
        else:
            print("  ⚠ CUDA not available (CPU mode will be used)")
    except:
        pass
    
    # Check configuration
    try:
        config = ConfigManager(config_path)
        config_issues = config.validate_config()
        if config_issues:
            issues.extend(config_issues)
        else:
            print("  ✓ Configuration valid")
    except Exception as e:
        issues.append(f"Configuration error: {str(e)}")
    
    # Check FFmpeg
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("  ✓ FFmpeg installed")
    except:
        issues.append("FFmpeg not found. Please install FFmpeg.")
    
    # Summary
    print("\n" + "="*50)
    if issues:
        print("❌ Installation issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    else:
        print("✅ Installation verified successfully!")
        return 0


def print_dry_run_info(args, config, components):
    """Print what would be done without executing"""
    print("\n" + "="*50)
    print("DRY RUN - No processing will be performed")
    print("="*50)
    
    print(f"\nInput video: {args.video}")
    print(f"Configuration: {args.config}")
    print(f"Profile: {args.profile}")
    
    print(f"\nActive models:")
    print(f"  - Vision-Language: {config.get('active_model')}")
    print(f"  - Whisper: {config.get('audio_models.whisper.model')}")
    print(f"  - Device: {config.get('pipeline.device')}")
    
    print(f"\nComponents to run: {', '.join(components)}")
    print(f"Output formats: {', '.join(args.output_formats)}")
    
    if args.output_dir:
        print(f"Output directory: {args.output_dir}")
    else:
        print("Output directory: Auto-generated")
    
    print("\nTo execute, remove the --dry-run flag")


if __name__ == "__main__":
    sys.exit(main())