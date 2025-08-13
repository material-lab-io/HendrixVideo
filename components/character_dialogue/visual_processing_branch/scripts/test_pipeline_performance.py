#!/usr/bin/env python3
"""
Comprehensive Performance Testing for Visual Pipeline

Tests the visual pipeline on long videos and generates detailed performance metrics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['TF_USE_LEGACY_KERAS'] = '1'

import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import psutil
import gc
from typing import Dict, List, Any

from tracked_visual_pipeline import TrackedVisualPipeline as VisualPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system resources during processing"""
    
    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.timestamps = []
        self.start_time = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.cpu_usage = []
        self.memory_usage = []
        self.timestamps = []
        
    def record(self):
        """Record current metrics"""
        if self.start_time is None:
            return
            
        self.timestamps.append(time.time() - self.start_time)
        self.cpu_usage.append(psutil.cpu_percent(interval=0.1))
        self.memory_usage.append(psutil.virtual_memory().percent)
        
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.cpu_usage:
            return {}
            
        return {
            'duration': self.timestamps[-1] if self.timestamps else 0,
            'cpu': {
                'avg': np.mean(self.cpu_usage),
                'max': np.max(self.cpu_usage),
                'std': np.std(self.cpu_usage)
            },
            'memory': {
                'avg': np.mean(self.memory_usage),
                'max': np.max(self.memory_usage),
                'std': np.std(self.memory_usage)
            }
        }


def test_video_segments(video_path: str, segment_duration: int = 300, 
                       output_dir: Path = None) -> Dict:
    """Test video in segments to analyze performance over time
    
    Args:
        video_path: Path to video file
        segment_duration: Duration of each segment in seconds
        output_dir: Output directory for results
        
    Returns:
        Dictionary with performance metrics
    """
    import cv2
    
    # Get video info
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    
    logger.info(f"Video duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    logger.info(f"Testing in {segment_duration}s segments")
    
    # Calculate segments
    num_segments = int(np.ceil(duration / segment_duration))
    segment_results = []
    
    # Initialize pipeline once
    pipeline = VisualPipeline()
    monitor = PerformanceMonitor()
    
    # Test each segment
    for i in range(min(num_segments, 3)):  # Test first 3 segments
        segment_start = i * segment_duration
        segment_end = min((i + 1) * segment_duration, duration)
        
        logger.info(f"\nTesting segment {i+1}/{num_segments} "
                   f"({segment_start:.1f}s - {segment_end:.1f}s)")
        
        # Create segment-specific output dir
        segment_dir = output_dir / f"segment_{i+1}"
        segment_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitor performance
        monitor.start()
        gc.collect()  # Clean memory before segment
        
        try:
            # Process segment
            start_time = time.time()
            results = pipeline.process_video(
                video_path,
                segment_dir,
                sample_rate=60,  # Sample every 2 seconds
                max_duration=segment_duration
            )
            
            # Record final metrics
            monitor.record()
            perf_stats = monitor.get_stats()
            
            # Add segment info
            results['segment'] = {
                'index': i + 1,
                'start_time': segment_start,
                'end_time': segment_end,
                'performance': perf_stats
            }
            
            segment_results.append(results)
            
        except Exception as e:
            logger.error(f"Segment {i+1} failed: {e}")
            segment_results.append({
                'segment': {'index': i+1},
                'error': str(e)
            })
    
    return {
        'video_info': {
            'path': video_path,
            'duration': duration,
            'fps': fps,
            'total_frames': total_frames
        },
        'test_config': {
            'segment_duration': segment_duration,
            'segments_tested': len(segment_results),
            'total_segments': num_segments
        },
        'segment_results': segment_results
    }


def analyze_performance_results(results: Dict, output_dir: Path):
    """Analyze and visualize performance results"""
    
    # Create performance plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Visual Pipeline Performance Analysis', fontsize=16)
    
    # Extract metrics from segments
    segments = results['segment_results']
    valid_segments = [s for s in segments if 'error' not in s]
    
    if not valid_segments:
        logger.error("No valid segments to analyze")
        return
    
    # 1. Processing speed over time
    ax = axes[0, 0]
    segment_nums = [s['segment']['index'] for s in valid_segments]
    processing_speeds = [s.get('processing_fps', 0) for s in valid_segments]
    
    ax.plot(segment_nums, processing_speeds, 'b-o', linewidth=2, markersize=8)
    ax.set_xlabel('Segment')
    ax.set_ylabel('Processing Speed (fps)')
    ax.set_title('Processing Speed by Segment')
    ax.grid(True, alpha=0.3)
    
    # 2. Detection rates
    ax = axes[0, 1]
    if all('stages' in s and 'detection' in s['stages'] for s in valid_segments):
        detection_rates = [s['stages']['detection']['detection_rate'] * 100 
                          for s in valid_segments]
        faces_detected = [s['stages']['detection']['faces_detected'] 
                         for s in valid_segments]
        
        ax.bar(segment_nums, detection_rates, alpha=0.7, label='Detection Rate %')
        ax2 = ax.twinx()
        ax2.plot(segment_nums, faces_detected, 'r-o', label='Faces Detected')
        ax.set_xlabel('Segment')
        ax.set_ylabel('Detection Rate (%)', color='b')
        ax2.set_ylabel('Faces Detected', color='r')
        ax.set_title('Detection Performance')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
    
    # 3. Embedding success rate
    ax = axes[1, 0]
    if all('stages' in s and 'embeddings' in s['stages'] for s in valid_segments):
        embedding_rates = [s['stages']['embeddings'].get('success_rate', 0) * 100 
                          for s in valid_segments]
        
        ax.bar(segment_nums, embedding_rates, color='green', alpha=0.7)
        ax.set_xlabel('Segment')
        ax.set_ylabel('Embedding Success Rate (%)')
        ax.set_title('Face Embedding Extraction Success')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
    
    # 4. Characters found
    ax = axes[1, 1]
    if all('stages' in s and 'clustering' in s['stages'] for s in valid_segments):
        characters_found = [s['stages']['clustering']['characters_found'] 
                           for s in valid_segments]
        
        ax.plot(segment_nums, characters_found, 'purple', marker='s', 
                markersize=10, linewidth=2)
        ax.set_xlabel('Segment')
        ax.set_ylabel('Unique Characters')
        ax.set_title('Character Identification')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'performance_analysis.png', dpi=150)
    plt.close()
    
    # Generate performance report
    report_path = output_dir / 'performance_report.md'
    with open(report_path, 'w') as f:
        f.write("# Visual Pipeline Performance Report\n\n")
        f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Video:** {Path(results['video_info']['path']).name}\n")
        f.write(f"**Duration:** {results['video_info']['duration']:.1f}s "
                f"({results['video_info']['duration']/60:.1f} minutes)\n\n")
        
        f.write("## Test Configuration\n\n")
        f.write(f"- Segment duration: {results['test_config']['segment_duration']}s\n")
        f.write(f"- Segments tested: {results['test_config']['segments_tested']}\n")
        f.write(f"- Total segments: {results['test_config']['total_segments']}\n\n")
        
        f.write("## Performance Summary\n\n")
        
        # Calculate aggregated metrics
        if valid_segments:
            avg_speed = np.mean([s.get('processing_fps', 0) for s in valid_segments])
            total_faces = sum(s['stages']['detection']['faces_detected'] 
                            for s in valid_segments 
                            if 'stages' in s and 'detection' in s['stages'])
            total_embeddings = sum(s['stages']['embeddings']['embeddings_extracted'] 
                                 for s in valid_segments 
                                 if 'stages' in s and 'embeddings' in s['stages'])
            
            f.write(f"- **Average processing speed:** {avg_speed:.2f} fps\n")
            f.write(f"- **Total faces detected:** {total_faces}\n")
            f.write(f"- **Total embeddings extracted:** {total_embeddings}\n")
            f.write(f"- **Embedding success rate:** "
                    f"{total_embeddings/total_faces*100:.1f}%\n\n" if total_faces > 0 else "N/A\n\n")
        
        f.write("## Segment Details\n\n")
        
        for seg in segments:
            idx = seg['segment']['index']
            f.write(f"### Segment {idx}\n\n")
            
            if 'error' in seg:
                f.write(f"**Error:** {seg['error']}\n\n")
                continue
            
            if 'stages' in seg:
                stages = seg['stages']
                
                if 'detection' in stages:
                    det = stages['detection']
                    f.write(f"**Detection:**\n")
                    f.write(f"- Frames processed: {det['frames_processed']}\n")
                    f.write(f"- Faces detected: {det['faces_detected']}\n")
                    f.write(f"- Detection rate: {det['detection_rate']*100:.1f}%\n")
                    f.write(f"- Processing time: {det['duration']:.2f}s\n\n")
                
                if 'embeddings' in stages:
                    emb = stages['embeddings']
                    f.write(f"**Embeddings:**\n")
                    f.write(f"- Extracted: {emb['embeddings_extracted']}\n")
                    f.write(f"- Success rate: {emb['success_rate']*100:.1f}%\n")
                    f.write(f"- Processing time: {emb['duration']:.2f}s\n\n")
                
                if 'clustering' in stages:
                    clust = stages['clustering']
                    f.write(f"**Clustering:**\n")
                    f.write(f"- Characters found: {clust['characters_found']}\n\n")
            
            if 'segment' in seg and 'performance' in seg['segment']:
                perf = seg['segment']['performance']
                f.write(f"**System Performance:**\n")
                f.write(f"- CPU usage: {perf['cpu']['avg']:.1f}% "
                        f"(max: {perf['cpu']['max']:.1f}%)\n")
                f.write(f"- Memory usage: {perf['memory']['avg']:.1f}% "
                        f"(max: {perf['memory']['max']:.1f}%)\n\n")
        
        f.write("## Recommendations\n\n")
        
        if valid_segments:
            if avg_speed < 1.0:
                f.write("- ⚠️ Processing speed is below 1 fps. Consider:\n")
                f.write("  - Using GPU acceleration\n")
                f.write("  - Increasing frame sampling rate\n")
                f.write("  - Reducing video resolution\n\n")
            
            if total_faces > 0 and total_embeddings / total_faces < 0.2:
                f.write("- ⚠️ Low embedding extraction rate. Consider:\n")
                f.write("  - Improving video quality\n")
                f.write("  - Adjusting face detection thresholds\n")
                f.write("  - Using face enhancement preprocessing\n\n")
            
            if avg_speed >= 1.0 and total_embeddings / total_faces >= 0.2:
                f.write("- ✅ Pipeline performance is satisfactory\n")
                f.write("- Ready for production use on similar content\n")
    
    logger.info(f"Performance report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Test pipeline performance")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--segment-duration", type=int, default=300,
                       help="Duration of each test segment (seconds)")
    parser.add_argument("--output", default="output/performance_test",
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output) / f"test_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Testing video: {args.video_path}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Run performance test
        results = test_video_segments(
            args.video_path,
            segment_duration=args.segment_duration,
            output_dir=output_dir
        )
        
        # Save raw results
        with open(output_dir / 'performance_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Analyze and visualize
        analyze_performance_results(results, output_dir)
        
        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE TEST COMPLETE")
        print("="*60)
        print(f"Video: {args.video_path}")
        print(f"Duration: {results['video_info']['duration']:.1f}s")
        print(f"Segments tested: {results['test_config']['segments_tested']}")
        
        valid_segments = [s for s in results['segment_results'] if 'error' not in s]
        if valid_segments:
            speeds = [s.get('processing_fps', 0) for s in valid_segments]
            print(f"\nAverage processing speed: {np.mean(speeds):.2f} fps")
            print(f"Speed range: {min(speeds):.2f} - {max(speeds):.2f} fps")
        
        print(f"\nDetailed results: {output_dir}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        raise


if __name__ == "__main__":
    main()