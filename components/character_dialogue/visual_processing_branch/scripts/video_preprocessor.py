#!/usr/bin/env python3
"""
Video Preprocessing Utility for Production Pipeline

Handles:
- Codec detection and conversion (AV1 -> H.264)
- Resolution checking and enhancement
- Quality assessment
- Batch processing
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoPreprocessor:
    """Handles video preprocessing for optimal face detection"""
    
    SUPPORTED_CODECS = ['h264', 'hevc', 'vp9', 'mpeg4']
    PROBLEM_CODECS = ['av1', 'vp8']
    
    def __init__(self, output_dir: str = 'preprocessed_videos'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def analyze_video(self, video_path: str) -> Dict:
        """Analyze video properties"""
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        logger.info(f"Analyzing video: {video_path}")
        
        # Get video info using ffprobe
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,duration,bit_rate',
            '-show_entries', 'format=duration,size',
            '-of', 'json',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            stream = info['streams'][0] if info.get('streams') else {}
            format_info = info.get('format', {})
            
            # Calculate FPS
            fps = 0
            if stream.get('avg_frame_rate'):
                num, den = map(int, stream['avg_frame_rate'].split('/'))
                fps = num / den if den > 0 else 0
            
            analysis = {
                'codec': stream.get('codec_name', 'unknown'),
                'width': int(stream.get('width', 0)),
                'height': int(stream.get('height', 0)),
                'fps': fps,
                'duration': float(format_info.get('duration', 0)),
                'size_mb': int(format_info.get('size', 0)) / (1024 * 1024),
                'bit_rate': int(stream.get('bit_rate', 0)),
                'needs_conversion': False,
                'issues': []
            }
            
            # Check for issues
            if analysis['codec'] in self.PROBLEM_CODECS:
                analysis['needs_conversion'] = True
                analysis['issues'].append(f"Unsupported codec: {analysis['codec']}")
            
            if analysis['width'] < 640 or analysis['height'] < 480:
                analysis['issues'].append(f"Low resolution: {analysis['width']}x{analysis['height']}")
            
            if analysis['fps'] < 15:
                analysis['issues'].append(f"Low frame rate: {analysis['fps']:.1f} fps")
            
            return analysis
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to analyze video: {e}")
            return {'error': str(e), 'needs_conversion': True, 'issues': ['Failed to analyze']}
    
    def convert_video(self, video_path: str, output_path: Optional[str] = None,
                     target_codec: str = 'h264', quality: str = 'high') -> str:
        """Convert video to compatible format"""
        
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = self.output_dir / f"{video_name}_converted.mp4"
        
        logger.info(f"Converting video to {target_codec}: {video_path} -> {output_path}")
        
        # Quality presets
        quality_presets = {
            'high': {'crf': 18, 'preset': 'slow'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'fast': {'crf': 28, 'preset': 'fast'}
        }
        
        preset = quality_presets.get(quality, quality_presets['medium'])
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg', '-i', video_path,
            '-c:v', f'lib{target_codec}',
            '-preset', preset['preset'],
            '-crf', str(preset['crf']),
            '-c:a', 'aac',  # Convert audio to AAC
            '-b:a', '192k',
            '-movflags', '+faststart',  # Enable streaming
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        try:
            # Run conversion with progress
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress
            for line in process.stderr:
                if 'time=' in line:
                    # Extract time for progress
                    time_str = line.split('time=')[1].split()[0]
                    print(f"\rConverting... {time_str}", end='', flush=True)
            
            process.wait()
            print()  # New line after progress
            
            if process.returncode == 0:
                logger.info(f"Conversion successful: {output_path}")
                return str(output_path)
            else:
                raise subprocess.CalledProcessError(process.returncode, cmd)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Conversion failed: {e}")
            raise
    
    def enhance_resolution(self, video_path: str, target_height: int = 720) -> str:
        """Upscale low-resolution videos"""
        
        analysis = self.analyze_video(video_path)
        
        if analysis['height'] >= target_height:
            logger.info(f"Video already at sufficient resolution: {analysis['height']}p")
            return video_path
        
        video_name = Path(video_path).stem
        output_path = self.output_dir / f"{video_name}_upscaled.mp4"
        
        logger.info(f"Upscaling video to {target_height}p")
        
        # Calculate target width maintaining aspect ratio
        aspect_ratio = analysis['width'] / analysis['height']
        target_width = int(target_height * aspect_ratio)
        
        # Ensure even dimensions
        target_width = target_width - (target_width % 2)
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f'scale={target_width}:{target_height}:flags=lanczos',
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Upscaling successful: {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Upscaling failed: {e}")
            raise
    
    def preprocess_video(self, video_path: str, 
                        convert_codec: bool = True,
                        enhance_resolution: bool = True,
                        target_height: int = 720) -> Dict:
        """Complete preprocessing pipeline"""
        
        logger.info(f"Preprocessing video: {video_path}")
        
        # Analyze original
        analysis = self.analyze_video(video_path)
        processed_path = video_path
        
        result = {
            'original': video_path,
            'processed': None,
            'analysis': analysis,
            'steps': []
        }
        
        # Convert codec if needed
        if convert_codec and analysis.get('needs_conversion'):
            try:
                processed_path = self.convert_video(processed_path)
                result['steps'].append('codec_conversion')
            except Exception as e:
                logger.error(f"Codec conversion failed: {e}")
                result['error'] = str(e)
                return result
        
        # Enhance resolution if needed
        if enhance_resolution and analysis.get('height', 0) < target_height:
            try:
                processed_path = self.enhance_resolution(processed_path, target_height)
                result['steps'].append('resolution_enhancement')
            except Exception as e:
                logger.error(f"Resolution enhancement failed: {e}")
                result['error'] = str(e)
        
        # Final analysis
        if processed_path != video_path:
            result['processed'] = processed_path
            result['final_analysis'] = self.analyze_video(processed_path)
        
        return result
    
    def batch_preprocess(self, video_list: list, **kwargs) -> list:
        """Preprocess multiple videos"""
        
        results = []
        for i, video_path in enumerate(video_list):
            logger.info(f"Processing video {i+1}/{len(video_list)}: {video_path}")
            result = self.preprocess_video(video_path, **kwargs)
            results.append(result)
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Video preprocessing for face detection pipeline")
    parser.add_argument('video', nargs='+', help='Video file(s) to preprocess')
    parser.add_argument('--output-dir', default='preprocessed_videos', help='Output directory')
    parser.add_argument('--no-convert', action='store_true', help='Skip codec conversion')
    parser.add_argument('--no-enhance', action='store_true', help='Skip resolution enhancement')
    parser.add_argument('--target-height', type=int, default=720, help='Target height for enhancement')
    parser.add_argument('--quality', choices=['high', 'medium', 'fast'], default='medium',
                       help='Conversion quality preset')
    
    args = parser.parse_args()
    
    # Initialize preprocessor
    preprocessor = VideoPreprocessor(args.output_dir)
    
    # Process videos
    for video_path in args.video:
        print(f"\n{'='*60}")
        print(f"Processing: {video_path}")
        print('='*60)
        
        try:
            result = preprocessor.preprocess_video(
                video_path,
                convert_codec=not args.no_convert,
                enhance_resolution=not args.no_enhance,
                target_height=args.target_height
            )
            
            # Print results
            print(f"\nOriginal video analysis:")
            for key, value in result['analysis'].items():
                if key not in ['needs_conversion', 'issues']:
                    print(f"  {key}: {value}")
            
            if result['analysis'].get('issues'):
                print(f"\nIssues found:")
                for issue in result['analysis']['issues']:
                    print(f"  - {issue}")
            
            if result.get('processed'):
                print(f"\nProcessed video: {result['processed']}")
                print(f"Steps performed: {', '.join(result['steps'])}")
                
                if result.get('final_analysis'):
                    print(f"\nFinal video analysis:")
                    for key, value in result['final_analysis'].items():
                        if key not in ['needs_conversion', 'issues']:
                            print(f"  {key}: {value}")
            else:
                print("\nNo preprocessing needed")
                
        except Exception as e:
            print(f"\nError processing video: {e}")
            logger.error(f"Failed to process {video_path}: {e}", exc_info=True)


if __name__ == "__main__":
    main()