#!/usr/bin/env python3
"""
Test enhanced visual pipeline on multiple videos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Test videos with their properties
TEST_VIDEOS = [
    {
        'path': '../test_video.mp4',
        'name': 'test_video_10s',
        'duration': 10,
        'resolution': '320x176',
        'description': 'Small resolution test video',
        'target_frames': 30
    },
    {
        'path': '../audio_processing_branch/test_video_10min.mp4',
        'name': 'test_video_10min',
        'duration': 600,  # Process first 10 minutes
        'resolution': '1920x1080',
        'description': 'HD video with AV1 codec',
        'target_frames': 150
    },
    {
        'path': 'output/performance_test/test_20250729_105517/segment_1/neural_network_30min_converted.mp4',
        'name': 'neural_network_segment',
        'duration': 300,  # Process first 5 minutes
        'resolution': 'Unknown',
        'description': 'Converted neural network video segment',
        'target_frames': 100
    }
]

def run_pipeline_test(video_info, output_base='output/multi_video_test'):
    """Run the enhanced pipeline on a video and collect results"""
    
    video_path = video_info['path']
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return None
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_base}/{video_info['name']}_{timestamp}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {video_info['name']}")
    print(f"Path: {video_path}")
    print(f"Description: {video_info['description']}")
    print(f"Target frames: {video_info['target_frames']}")
    print(f"{'='*60}")
    
    # Run the pipeline
    cmd = [
        'python', 'scripts/tracked_visual_pipeline.py',
        video_path,
        '--output', output_dir,
        '--target-frames', str(video_info['target_frames']),
        '--extraction-mode', 'intelligent'
    ]
    
    start_time = time.time()
    
    try:
        # Run with timeout based on video duration
        timeout = max(300, video_info['duration'] * 2)  # At least 5 minutes
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'TF_USE_LEGACY_KERAS': '1'}
        )
        
        processing_time = time.time() - start_time
        
        if result.returncode != 0:
            print(f"Pipeline failed with error:")
            print(result.stderr[-1000:])  # Last 1000 chars of error
            return {
                'video': video_info['name'],
                'status': 'failed',
                'error': result.stderr[-1000:],
                'processing_time': processing_time
            }
        
        # Read results
        schema_path = Path(output_dir) / 'character_data_schemaC.json'
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
            
            # Extract key metrics
            results = {
                'video': video_info['name'],
                'status': 'success',
                'processing_time': processing_time,
                'frames_analyzed': schema_data['metadata'].get('frames_analyzed', 0),
                'characters_detected': len(schema_data['characters']),
                'total_detections': len(schema_data['detections']),
                'character_details': []
            }
            
            # Get character details
            for char_id, char_info in schema_data['characters'].items():
                results['character_details'].append({
                    'id': char_id,
                    'appearances': char_info['num_appearances'],
                    'screen_time': char_info['total_screen_time'],
                    'time_range': f"{char_info['first_appearance']:.1f}s - {char_info['last_appearance']:.1f}s"
                })
            
            # Sort by screen time
            results['character_details'].sort(key=lambda x: x['screen_time'], reverse=True)
            
            return results
        else:
            return {
                'video': video_info['name'],
                'status': 'no_output',
                'processing_time': processing_time
            }
            
    except subprocess.TimeoutExpired:
        return {
            'video': video_info['name'],
            'status': 'timeout',
            'processing_time': time.time() - start_time
        }
    except Exception as e:
        return {
            'video': video_info['name'],
            'status': 'error',
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def generate_report(all_results):
    """Generate a comprehensive test report"""
    
    report = []
    report.append("# Multi-Video Test Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n## Summary")
    
    # Count statuses
    success_count = sum(1 for r in all_results if r['status'] == 'success')
    failed_count = sum(1 for r in all_results if r['status'] != 'success')
    
    report.append(f"- Total videos tested: {len(all_results)}")
    report.append(f"- Successful: {success_count}")
    report.append(f"- Failed: {failed_count}")
    
    # Individual results
    report.append("\n## Individual Results")
    
    for result in all_results:
        report.append(f"\n### {result['video']}")
        report.append(f"- Status: {result['status']}")
        report.append(f"- Processing time: {result['processing_time']:.1f}s")
        
        if result['status'] == 'success':
            report.append(f"- Frames analyzed: {result['frames_analyzed']}")
            report.append(f"- Characters detected: {result['characters_detected']}")
            report.append(f"- Total detections: {result['total_detections']}")
            
            if result['character_details']:
                report.append("\n**Character Details:**")
                for char in result['character_details']:
                    report.append(f"- Character {char['id']}: {char['appearances']} appearances, "
                                f"{char['screen_time']:.1f}s screen time ({char['time_range']})")
        
        elif result['status'] == 'failed':
            report.append(f"- Error: {result.get('error', 'Unknown error')}")
    
    # Analysis
    report.append("\n## Analysis")
    
    if success_count > 0:
        # Calculate averages for successful runs
        successful_results = [r for r in all_results if r['status'] == 'success']
        
        avg_processing_time = sum(r['processing_time'] for r in successful_results) / len(successful_results)
        avg_characters = sum(r['characters_detected'] for r in successful_results) / len(successful_results)
        total_characters = sum(r['characters_detected'] for r in successful_results)
        
        report.append(f"\n### Performance Metrics")
        report.append(f"- Average processing time: {avg_processing_time:.1f}s")
        report.append(f"- Average characters per video: {avg_characters:.1f}")
        report.append(f"- Total unique characters detected: {total_characters}")
        
        # Check for videos with no characters
        no_char_videos = [r for r in successful_results if r['characters_detected'] == 0]
        if no_char_videos:
            report.append(f"\n### Videos with no characters detected:")
            for video in no_char_videos:
                report.append(f"- {video['video']}")
    
    return "\n".join(report)

def main():
    """Run tests on all available videos"""
    
    print("Starting multi-video test suite...")
    print(f"Testing {len(TEST_VIDEOS)} videos")
    
    # Ensure we're in the right directory
    os.chdir('/home/hardik/audio_analysis/visual_processing_branch')
    
    all_results = []
    
    for video_info in TEST_VIDEOS:
        result = run_pipeline_test(video_info)
        if result:
            all_results.append(result)
            
            # Quick summary
            if result['status'] == 'success':
                print(f"✅ Success: {result['characters_detected']} characters detected")
            else:
                print(f"❌ Failed: {result['status']}")
    
    # Generate and save report
    report = generate_report(all_results)
    
    report_path = f"output/multi_video_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {report_path}")
    print("\n" + "="*60)
    print("Test Summary:")
    print(report.split("## Analysis")[0])

if __name__ == "__main__":
    main()