#!/usr/bin/env python3
"""
Test enhanced visual pipeline on videos with proper parameters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

def test_video(video_path, name, target_frames=100):
    """Test a single video with the enhanced pipeline"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Video: {video_path}")
    print(f"Target frames: {target_frames}")
    print(f"{'='*60}")
    
    # Check if video exists
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return None
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output/video_tests/{name}_{timestamp}"
    
    # Run the pipeline
    cmd = [
        'python', 'scripts/tracked_visual_pipeline.py',
        video_path,
        '--output', output_dir,
        '--target-frames', str(target_frames),
        '--extraction-mode', 'uniform'  # Use uniform for better coverage
    ]
    
    start_time = time.time()
    
    try:
        # Set environment
        env = os.environ.copy()
        env['TF_USE_LEGACY_KERAS'] = '1'
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        processing_time = time.time() - start_time
        
        # Check if schema was created
        schema_path = Path(output_dir) / 'character_data_schemaC.json'
        
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
            
            # Print results
            print(f"\n✅ Pipeline completed in {processing_time:.1f}s")
            print(f"📊 Results:")
            print(f"   - Frames analyzed: {schema_data['metadata'].get('frames_analyzed', 0)}")
            print(f"   - Characters detected: {len(schema_data['characters'])}")
            print(f"   - Total face detections: {len(schema_data['detections'])}")
            
            # Character details
            if schema_data['characters']:
                print(f"\n👥 Character Details:")
                for char_id, char_info in schema_data['characters'].items():
                    print(f"   Character {char_id}:")
                    print(f"     - Appearances: {char_info['num_appearances']}")
                    print(f"     - Screen time: {char_info['total_screen_time']:.1f}s")
                    print(f"     - Time range: {char_info['first_appearance']:.1f}s - {char_info['last_appearance']:.1f}s")
                    if char_info.get('attributes'):
                        print(f"     - Attributes: {char_info['attributes']}")
            else:
                print(f"\n⚠️  No characters detected")
                
            return {
                'success': True,
                'characters': len(schema_data['characters']),
                'detections': len(schema_data['detections']),
                'frames': schema_data['metadata'].get('frames_analyzed', 0),
                'time': processing_time
            }
        else:
            print(f"\n❌ Pipeline failed - no output generated")
            if result.stderr:
                print(f"Error: {result.stderr[-500:]}")
            return {
                'success': False,
                'error': result.stderr[-500:] if result.stderr else 'Unknown error',
                'time': processing_time
            }
            
    except subprocess.TimeoutExpired:
        print(f"\n❌ Pipeline timed out after 5 minutes")
        return {
            'success': False,
            'error': 'Timeout',
            'time': 300
        }
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'time': time.time() - start_time
        }

def main():
    """Test multiple videos"""
    
    print("Enhanced Visual Pipeline - Video Test Suite")
    print("==========================================")
    
    # Change to correct directory
    os.chdir('/home/hardik/audio_analysis/visual_processing_branch')
    
    # Test videos
    test_cases = [
        {
            'path': '../test_video.mp4',
            'name': 'test_video_10s',
            'frames': 100  # More frames for better detection
        },
        {
            'path': '../audio_processing_branch/test_video.mp4',  # Try the other copy
            'name': 'test_video_copy',
            'frames': 100
        }
    ]
    
    # First, let's check for AV1 codec issue
    print("\n🔍 Checking video codecs...")
    for test in test_cases:
        if os.path.exists(test['path']):
            cmd = f"ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {test['path']}"
            codec = subprocess.check_output(cmd, shell=True, text=True).strip()
            print(f"   {test['name']}: {codec} codec")
            
            # If AV1, we need to convert
            if codec == 'av1':
                print(f"   ⚠️  AV1 codec detected - may need conversion")
                # Add conversion step
                converted_path = f"output/video_tests/{test['name']}_h264.mp4"
                print(f"   Converting to H.264...")
                convert_cmd = f"ffmpeg -i {test['path']} -c:v libx264 -preset fast -crf 23 -c:a copy {converted_path} -y"
                try:
                    subprocess.run(convert_cmd, shell=True, check=True, capture_output=True)
                    test['path'] = converted_path
                    print(f"   ✅ Converted successfully")
                except:
                    print(f"   ❌ Conversion failed")
    
    # Run tests
    results = []
    for test in test_cases:
        if os.path.exists(test['path']):
            result = test_video(test['path'], test['name'], test['frames'])
            if result:
                results.append({'name': test['name'], **result})
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r['success'])
    print(f"Total tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    
    print("\nDetailed Results:")
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"\n{status} {r['name']}:")
        if r['success']:
            print(f"   - Characters: {r['characters']}")
            print(f"   - Detections: {r['detections']}")
            print(f"   - Frames: {r['frames']}")
            print(f"   - Time: {r['time']:.1f}s")
        else:
            print(f"   - Error: {r.get('error', 'Unknown')}")

if __name__ == "__main__":
    main()