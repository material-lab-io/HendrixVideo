#!/usr/bin/env python3
"""
Video Converter with AV1 Codec Support

Converts videos to a compatible format for processing, handling AV1 codec issues.
"""

import subprocess
import argparse
import logging
from pathlib import Path
import json
import time
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoConverter:
    """Handles video conversion with codec detection and fallback strategies"""
    
    def __init__(self):
        self.supported_codecs = ['h264', 'h265', 'vp9', 'mpeg4']
        self.problematic_codecs = ['av1', 'av01']
        
    def get_video_info(self, video_path: str) -> dict:
        """Get video codec and format information"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in info.get('streams', []):
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                return {
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'codec_long': video_stream.get('codec_long_name', ''),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                    'duration': float(info.get('format', {}).get('duration', 0)),
                    'bitrate': int(info.get('format', {}).get('bit_rate', 0)),
                    'size': int(info.get('format', {}).get('size', 0))
                }
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
    
    def check_codec_compatibility(self, video_path: str) -> tuple:
        """Check if video codec is compatible
        
        Returns:
            (is_compatible, codec_info)
        """
        info = self.get_video_info(video_path)
        
        if not info:
            return False, None
        
        codec = info['codec'].lower()
        
        # Check if codec is problematic
        if any(prob in codec for prob in self.problematic_codecs):
            logger.warning(f"Problematic codec detected: {info['codec']} ({info['codec_long']})")
            return False, info
        
        # Check if codec is supported
        if codec in self.supported_codecs:
            logger.info(f"Compatible codec: {info['codec']}")
            return True, info
        
        logger.warning(f"Unknown codec compatibility: {info['codec']}")
        return False, info
    
    def convert_video(self, input_path: str, output_path: str, 
                     target_codec: str = 'h264',
                     quality: str = 'medium',
                     progress_callback=None) -> bool:
        """Convert video to compatible format
        
        Args:
            input_path: Input video path
            output_path: Output video path
            target_codec: Target codec (h264, h265, vp9)
            quality: Quality preset (fast, medium, slow)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Success status
        """
        logger.info(f"Converting video: {input_path} -> {output_path}")
        logger.info(f"Target codec: {target_codec}, Quality: {quality}")
        
        # Build ffmpeg command
        cmd = ['ffmpeg']
        
        # Hardware acceleration if available (must come before -i)
        if self._check_hardware_acceleration():
            cmd.extend(['-hwaccel', 'auto'])
        
        # Input file
        cmd.extend(['-i', input_path])
        
        # Codec-specific settings
        if target_codec == 'h264':
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', quality,
                '-crf', '23',  # Good quality
                '-profile:v', 'high',
                '-level', '4.1'
            ])
        elif target_codec == 'h265':
            cmd.extend([
                '-c:v', 'libx265',
                '-preset', quality,
                '-crf', '28'
            ])
        elif target_codec == 'vp9':
            cmd.extend([
                '-c:v', 'libvpx-vp9',
                '-crf', '30',
                '-b:v', '0'
            ])
        else:
            logger.error(f"Unsupported target codec: {target_codec}")
            return False
        
        # Copy audio without re-encoding
        cmd.extend(['-c:a', 'copy'])
        
        # Add progress tracking
        cmd.extend(['-progress', 'pipe:1'])
        
        # Overwrite output
        cmd.extend(['-y', output_path])
        
        # Run conversion
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Track progress
            duration = None
            for line in process.stdout:
                if line.startswith('duration='):
                    if duration is None:
                        # Get total duration from first progress line
                        parts = line.strip().split('=')
                        if len(parts) == 2:
                            try:
                                # Parse duration in format HH:MM:SS.MS
                                time_str = parts[1]
                                h, m, s = time_str.split(':')
                                duration = int(h) * 3600 + int(m) * 60 + float(s)
                            except:
                                pass
                
                if line.startswith('out_time_ms='):
                    try:
                        current_ms = int(line.split('=')[1])
                        current_sec = current_ms / 1000000
                        
                        if duration and progress_callback:
                            progress = min(current_sec / duration, 1.0)
                            progress_callback(progress)
                    except:
                        pass
            
            # Wait for completion
            process.wait()
            
            if process.returncode == 0:
                logger.info("Conversion completed successfully")
                return True
            else:
                stderr = process.stderr.read()
                logger.error(f"Conversion failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return False
    
    def _check_hardware_acceleration(self) -> bool:
        """Check if hardware acceleration is available"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hwaccels'],
                capture_output=True,
                text=True
            )
            return 'cuda' in result.stdout or 'vaapi' in result.stdout
        except:
            return False
    
    def convert_if_needed(self, video_path: str, output_dir: str = None) -> str:
        """Convert video if codec is incompatible
        
        Returns:
            Path to processed video (original or converted)
        """
        is_compatible, info = self.check_codec_compatibility(video_path)
        
        if is_compatible:
            logger.info("Video codec is compatible, no conversion needed")
            return video_path
        
        # Need conversion
        video_path = Path(video_path)
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = video_path.parent
        
        # Generate output filename
        output_path = output_dir / f"{video_path.stem}_converted.mp4"
        
        # Check if already converted
        if output_path.exists():
            logger.info(f"Using existing converted video: {output_path}")
            return str(output_path)
        
        # Show progress
        def show_progress(progress):
            percent = int(progress * 100)
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'\rConverting: [{bar}] {percent}%', end='', flush=True)
        
        logger.info(f"Converting {info['codec']} video to H.264...")
        start_time = time.time()
        
        success = self.convert_video(
            str(video_path),
            str(output_path),
            target_codec='h264',
            quality='medium',
            progress_callback=show_progress
        )
        
        print()  # New line after progress bar
        
        if success:
            elapsed = time.time() - start_time
            size_reduction = (1 - output_path.stat().st_size / info['size']) * 100
            logger.info(f"Conversion completed in {elapsed:.1f}s")
            logger.info(f"Size reduction: {size_reduction:.1f}%")
            return str(output_path)
        else:
            logger.error("Conversion failed")
            return video_path


def main():
    parser = argparse.ArgumentParser(description="Convert video for compatibility")
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument("--output-dir", help="Output directory (default: same as input)")
    parser.add_argument("--codec", default="h264", 
                       choices=['h264', 'h265', 'vp9'],
                       help="Target codec")
    parser.add_argument("--quality", default="medium",
                       choices=['fast', 'medium', 'slow'],
                       help="Encoding quality preset")
    parser.add_argument("--force", action="store_true",
                       help="Force conversion even if compatible")
    
    args = parser.parse_args()
    
    converter = VideoConverter()
    
    # Check current codec
    is_compatible, info = converter.check_codec_compatibility(args.video_path)
    
    if info:
        print(f"\nVideo Information:")
        print(f"  Codec: {info['codec']} ({info['codec_long']})")
        print(f"  Resolution: {info['width']}x{info['height']}")
        print(f"  Duration: {info['duration']:.1f}s")
        print(f"  Size: {info['size'] / (1024*1024):.1f} MB")
        print(f"  Compatible: {'Yes' if is_compatible else 'No'}")
    
    if is_compatible and not args.force:
        print("\nVideo is already compatible. Use --force to convert anyway.")
        return
    
    # Convert video
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{Path(args.video_path).stem}_converted.mp4"
    else:
        output_path = Path(args.video_path).parent / f"{Path(args.video_path).stem}_converted.mp4"
    
    print(f"\nConverting to {args.codec}...")
    
    def show_progress(progress):
        percent = int(progress * 100)
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f'\r[{bar}] {percent}%', end='', flush=True)
    
    success = converter.convert_video(
        args.video_path,
        str(output_path),
        target_codec=args.codec,
        quality=args.quality,
        progress_callback=show_progress
    )
    
    print()  # New line
    
    if success:
        print(f"\n✓ Conversion complete: {output_path}")
        
        # Check new file
        new_info = converter.get_video_info(str(output_path))
        if new_info:
            print(f"\nConverted Video:")
            print(f"  Codec: {new_info['codec']}")
            print(f"  Size: {new_info['size'] / (1024*1024):.1f} MB")
    else:
        print("\n✗ Conversion failed")


if __name__ == "__main__":
    main()