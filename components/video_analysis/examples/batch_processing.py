#!/usr/bin/env python3
"""
Batch processing example for analyzing multiple videos.

Usage:
    python examples/batch_processing.py path/to/video/directory/
"""

import sys
import argparse
import glob
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import VideoAnalysisPipeline


def process_single_video(video_path, config_path, output_base_dir):
    """Process a single video file."""
    video_name = Path(video_path).stem
    output_dir = Path(output_base_dir) / video_name
    
    print(f"Processing: {video_path}")
    
    try:
        pipeline = VideoAnalysisPipeline(config_path)
        results = pipeline.analyze_video(video_path, output_dir=str(output_dir))
        
        # Return summary statistics
        return {
            'video': video_path,
            'status': 'success',
            'shots': len(results.get('shots', [])),
            'scenes': len(results.get('scenes', [])),
            'duration': results.get('shots', [{}])[-1].end if results.get('shots') else 0
        }
    except Exception as e:
        return {
            'video': video_path,
            'status': 'failed',
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Batch process multiple videos")
    parser.add_argument("directory", help="Directory containing video files")
    parser.add_argument("--pattern", default="*.mp4", help="File pattern to match (default: *.mp4)")
    parser.add_argument("--output-dir", default="batch_output", help="Base output directory")
    parser.add_argument("--config", default="config.yaml", help="Configuration file")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers")
    parser.add_argument("--dry-run", action="store_true", help="List files without processing")
    args = parser.parse_args()
    
    # Find video files
    video_dir = Path(args.directory)
    if not video_dir.exists():
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)
    
    # Get all video files matching pattern
    video_files = []
    for pattern in args.pattern.split(','):
        video_files.extend(glob.glob(str(video_dir / pattern.strip())))
    
    video_files = sorted(set(video_files))  # Remove duplicates and sort
    
    if not video_files:
        print(f"No video files found matching pattern: {args.pattern}")
        sys.exit(1)
    
    print(f"Found {len(video_files)} video files")
    
    if args.dry_run:
        print("\nFiles to process:")
        for i, video in enumerate(video_files, 1):
            print(f"  {i}. {video}")
        return
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine number of workers
    num_workers = args.workers or min(multiprocessing.cpu_count(), len(video_files))
    print(f"Using {num_workers} parallel workers")
    
    # Process videos in parallel
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_video = {
            executor.submit(
                process_single_video, 
                video, 
                args.config, 
                args.output_dir
            ): video 
            for video in video_files
        }
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_video):
            completed += 1
            video = future_to_video[future]
            
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] == 'success':
                    print(f"[{completed}/{len(video_files)}] ✓ {Path(video).name} - "
                          f"{result['shots']} shots, {result['scenes']} scenes")
                else:
                    print(f"[{completed}/{len(video_files)}] ✗ {Path(video).name} - "
                          f"Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"[{completed}/{len(video_files)}] ✗ {Path(video).name} - "
                      f"Exception: {e}")
    
    # Summary
    elapsed_time = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    print("\n" + "=" * 50)
    print("Batch Processing Complete!")
    print(f"  Total videos: {len(video_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {elapsed_time:.2f} seconds")
    print(f"  Average time per video: {elapsed_time / len(video_files):.2f} seconds")
    
    # Save summary report
    report_path = Path(args.output_dir) / "batch_report.txt"
    with open(report_path, 'w') as f:
        f.write("Batch Processing Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total videos: {len(video_files)}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Total time: {elapsed_time:.2f} seconds\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-" * 50 + "\n")
        
        for result in results:
            video_name = Path(result['video']).name
            if result['status'] == 'success':
                f.write(f"{video_name}: SUCCESS\n")
                f.write(f"  Shots: {result['shots']}\n")
                f.write(f"  Scenes: {result['scenes']}\n")
                f.write(f"  Duration: {result['duration']:.2f}s\n")
            else:
                f.write(f"{video_name}: FAILED\n")
                f.write(f"  Error: {result.get('error', 'Unknown')}\n")
            f.write("\n")
    
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()