#!/usr/bin/env python3
"""
Performance benchmarking script for Hendrix Video Analysis Pipeline.

Usage:
    python examples/benchmark.py
"""

import sys
import time
import psutil
import torch
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import VideoAnalysisPipeline
from tests.create_test_video import create_test_video


class PerformanceBenchmark:
    """Benchmark pipeline performance."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'benchmarks': []
        }
    
    def get_system_info(self):
        """Collect system information."""
        info = {
            'cpu': {
                'model': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else 'Unknown',
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(logical=True),
            },
            'memory': {
                'total_gb': psutil.virtual_memory().total / (1024**3),
                'available_gb': psutil.virtual_memory().available / (1024**3),
            },
            'gpu': {
                'available': torch.cuda.is_available(),
            }
        }
        
        if torch.cuda.is_available():
            info['gpu'].update({
                'name': torch.cuda.get_device_name(0),
                'memory_gb': torch.cuda.get_device_properties(0).total_memory / (1024**3),
                'compute_capability': f"{torch.cuda.get_device_properties(0).major}.{torch.cuda.get_device_properties(0).minor}"
            })
        
        return info
    
    def benchmark_video(self, video_path, config_path, name):
        """Benchmark a single video."""
        print(f"\nBenchmarking: {name}")
        print("-" * 40)
        
        # Memory before
        mem_before = psutil.virtual_memory().used / (1024**3)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            vram_before = torch.cuda.memory_allocated() / (1024**3)
        else:
            vram_before = 0
        
        # Initialize pipeline
        init_start = time.time()
        pipeline = VideoAnalysisPipeline(config_path)
        init_time = time.time() - init_start
        
        # Stage timings
        stage_times = {}
        total_start = time.time()
        
        # Shot detection
        stage_start = time.time()
        pipeline.shot_detector.detect_shots(video_path)
        stage_times['shot_detection'] = time.time() - stage_start
        
        # Get video info
        from src.utils.video_processor import VideoProcessor
        vp = VideoProcessor(video_path)
        metadata = vp.get_metadata()
        
        # Full pipeline
        pipeline_start = time.time()
        results = pipeline.analyze_video(video_path)
        total_time = time.time() - pipeline_start
        
        # Memory after
        mem_after = psutil.virtual_memory().used / (1024**3)
        if torch.cuda.is_available():
            vram_after = torch.cuda.memory_allocated() / (1024**3)
        else:
            vram_after = 0
        
        # Calculate metrics
        benchmark = {
            'name': name,
            'video': {
                'duration_s': metadata['duration'],
                'fps': metadata['fps'],
                'resolution': f"{metadata['width']}x{metadata['height']}",
                'total_frames': metadata['total_frames']
            },
            'results': {
                'shots': len(results.get('shots', [])),
                'scenes': len(results.get('scenes', []))
            },
            'timing': {
                'initialization_s': init_time,
                'total_pipeline_s': total_time,
                'shot_detection_s': stage_times['shot_detection'],
                'fps_processed': metadata['total_frames'] / total_time
            },
            'memory': {
                'ram_used_gb': mem_after - mem_before,
                'vram_used_gb': vram_after - vram_before,
                'peak_ram_gb': psutil.virtual_memory().used / (1024**3)
            }
        }
        
        # Print summary
        print(f"  Video: {metadata['duration']:.2f}s, {metadata['total_frames']} frames")
        print(f"  Results: {benchmark['results']['shots']} shots, {benchmark['results']['scenes']} scenes")
        print(f"  Time: {total_time:.2f}s total ({benchmark['timing']['fps_processed']:.1f} fps)")
        print(f"  Memory: {benchmark['memory']['ram_used_gb']:.2f} GB RAM")
        if torch.cuda.is_available():
            print(f"  VRAM: {benchmark['memory']['vram_used_gb']:.2f} GB")
        
        return benchmark
    
    def run_benchmarks(self):
        """Run all benchmarks."""
        print("Hendrix Video Analysis Pipeline - Performance Benchmark")
        print("=" * 60)
        
        # Create test videos
        print("\nCreating test videos...")
        test_videos = []
        
        # Short video
        video_path, frames, duration = create_test_video(
            'benchmark_short.mp4',
            width=640, height=480, fps=30
        )
        test_videos.append(('Short Video (640x480, 16s)', video_path))
        
        # HD video
        video_path, frames, duration = create_test_video(
            'benchmark_hd.mp4',
            width=1280, height=720, fps=30
        )
        test_videos.append(('HD Video (1280x720, 16s)', video_path))
        
        # Run benchmarks
        for name, video_path in test_videos:
            try:
                # Test with GPU if available
                if torch.cuda.is_available():
                    gpu_benchmark = self.benchmark_video(video_path, 'config.yaml', f"{name} - GPU")
                    self.results['benchmarks'].append(gpu_benchmark)
                
                # Test with CPU
                cpu_config = 'config.yaml'  # Could create CPU-specific config
                cpu_benchmark = self.benchmark_video(video_path, cpu_config, f"{name} - CPU")
                self.results['benchmarks'].append(cpu_benchmark)
                
            except Exception as e:
                print(f"  Failed: {e}")
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save benchmark results."""
        output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
    
    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        print(f"\nSystem: {self.results['system_info']['cpu']['cores']} cores, "
              f"{self.results['system_info']['memory']['total_gb']:.1f} GB RAM")
        
        if self.results['system_info']['gpu']['available']:
            print(f"GPU: {self.results['system_info']['gpu']['name']} "
                  f"({self.results['system_info']['gpu']['memory_gb']:.1f} GB)")
        
        print("\nPerformance Results:")
        print("-" * 60)
        print(f"{'Configuration':<30} {'FPS':<10} {'Time (s)':<10} {'RAM (GB)':<10}")
        print("-" * 60)
        
        for benchmark in self.results['benchmarks']:
            name = benchmark['name'][:30]
            fps = benchmark['timing']['fps_processed']
            time_s = benchmark['timing']['total_pipeline_s']
            ram_gb = benchmark['memory']['ram_used_gb']
            
            print(f"{name:<30} {fps:<10.1f} {time_s:<10.2f} {ram_gb:<10.2f}")
        
        # Clean up test videos
        for _, video_path in test_videos:
            Path(video_path).unlink(missing_ok=True)


def main():
    """Run performance benchmarks."""
    benchmark = PerformanceBenchmark()
    benchmark.run_benchmarks()


if __name__ == "__main__":
    main()