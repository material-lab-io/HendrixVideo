#!/usr/bin/env python3
"""
Download high-quality test videos for production testing

Sources:
- Open source movie trailers
- Public domain films
- Creative Commons content
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import requests
from typing import List, Dict
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoDownloader:
    """Downloads test videos from various sources"""
    
    # High-quality test videos with dialogue and multiple characters
    TEST_VIDEOS = [
        {
            'name': 'big_buck_bunny_trailer',
            'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            'duration': 60,
            'resolution': '1080p',
            'description': 'Animated short with character interactions',
            'has_dialogue': False  # Animated, but good for face detection testing
        },
        {
            'name': 'sintel_trailer', 
            'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4',
            'duration': 52,
            'resolution': '1080p',
            'description': 'Blender open movie trailer with human characters',
            'has_dialogue': True
        },
        {
            'name': 'tears_of_steel_trailer',
            'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
            'duration': 12,
            'resolution': '1080p', 
            'description': 'Sci-fi short with dialogue and action',
            'has_dialogue': True
        },
        {
            'name': 'elephants_dream',
            'url': 'http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
            'duration': 60,
            'resolution': '1080p',
            'description': 'Surreal animation with character dialogue',
            'has_dialogue': True
        }
    ]
    
    def __init__(self, output_dir: str = 'test_videos'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def download_video(self, video_info: Dict) -> str:
        """Download a single video"""
        
        output_path = self.output_dir / f"{video_info['name']}.mp4"
        
        if output_path.exists():
            logger.info(f"Video already exists: {output_path}")
            return str(output_path)
        
        logger.info(f"Downloading: {video_info['name']}")
        logger.info(f"URL: {video_info['url']}")
        logger.info(f"Description: {video_info['description']}")
        
        try:
            # Download using requests with progress bar
            response = requests.get(video_info['url'], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress bar
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", 
                                  end='', flush=True)
            
            print()  # New line after progress
            logger.info(f"Downloaded successfully: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to download {video_info['name']}: {e}")
            if output_path.exists():
                output_path.unlink()  # Remove partial download
            raise
    
    def download_all(self) -> List[str]:
        """Download all test videos"""
        
        downloaded_paths = []
        
        for video_info in self.TEST_VIDEOS:
            try:
                path = self.download_video(video_info)
                downloaded_paths.append(path)
            except Exception as e:
                logger.error(f"Skipping {video_info['name']}: {e}")
        
        return downloaded_paths
    
    def verify_downloads(self) -> Dict:
        """Verify downloaded videos"""
        
        results = {}
        
        for video_info in self.TEST_VIDEOS:
            video_path = self.output_dir / f"{video_info['name']}.mp4"
            
            if video_path.exists():
                # Get actual properties using ffprobe
                cmd = [
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height,codec_name',
                    '-show_entries', 'format=duration',
                    '-of', 'json',
                    str(video_path)
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    info = json.loads(result.stdout)
                    
                    stream = info['streams'][0]
                    format_info = info['format']
                    
                    results[video_info['name']] = {
                        'exists': True,
                        'path': str(video_path),
                        'size_mb': video_path.stat().st_size / (1024 * 1024),
                        'codec': stream['codec_name'],
                        'resolution': f"{stream['width']}x{stream['height']}",
                        'duration': float(format_info['duration']),
                        'has_dialogue': video_info['has_dialogue']
                    }
                except Exception as e:
                    results[video_info['name']] = {
                        'exists': True,
                        'path': str(video_path),
                        'error': str(e)
                    }
            else:
                results[video_info['name']] = {'exists': False}
        
        return results


def download_youtube_samples():
    """Download samples from YouTube (requires yt-dlp)"""
    
    logger.info("Checking for yt-dlp...")
    
    # Check if yt-dlp is installed
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
        return []
    
    # YouTube samples with good dialogue scenes
    youtube_samples = [
        {
            'name': 'movie_scene_dialogue',
            'url': 'https://www.youtube.com/watch?v=example',  # Replace with actual URLs
            'start_time': '00:00:30',
            'duration': 60,
            'description': 'Movie scene with clear dialogue'
        }
    ]
    
    output_dir = Path('test_videos/youtube')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    
    for sample in youtube_samples:
        output_path = output_dir / f"{sample['name']}.mp4"
        
        if output_path.exists():
            logger.info(f"Already exists: {output_path}")
            downloaded.append(str(output_path))
            continue
        
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '--merge-output-format', 'mp4',
            '-o', str(output_path),
            sample['url']
        ]
        
        # Add time range if specified
        if 'start_time' in sample:
            cmd.extend(['--postprocessor-args', 
                       f"ffmpeg:-ss {sample['start_time']} -t {sample['duration']}"])
        
        try:
            logger.info(f"Downloading YouTube sample: {sample['name']}")
            subprocess.run(cmd, check=True)
            downloaded.append(str(output_path))
        except Exception as e:
            logger.error(f"Failed to download {sample['name']}: {e}")
    
    return downloaded


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download test videos for production testing")
    parser.add_argument('--output-dir', default='test_videos', help='Output directory')
    parser.add_argument('--youtube', action='store_true', help='Also download YouTube samples')
    parser.add_argument('--verify-only', action='store_true', help='Only verify existing downloads')
    
    args = parser.parse_args()
    
    downloader = VideoDownloader(args.output_dir)
    
    if args.verify_only:
        # Just verify existing downloads
        results = downloader.verify_downloads()
        
        print("\nDownloaded Videos Status:")
        print("=" * 80)
        
        for name, info in results.items():
            print(f"\n{name}:")
            if info['exists']:
                print(f"  Path: {info.get('path')}")
                print(f"  Size: {info.get('size_mb', 0):.1f} MB")
                print(f"  Resolution: {info.get('resolution', 'Unknown')}")
                print(f"  Duration: {info.get('duration', 0):.1f}s")
                print(f"  Codec: {info.get('codec', 'Unknown')}")
                print(f"  Has Dialogue: {info.get('has_dialogue', False)}")
                
                if 'error' in info:
                    print(f"  Error: {info['error']}")
            else:
                print("  Status: Not downloaded")
    else:
        # Download videos
        print("Downloading test videos...")
        print("=" * 80)
        
        paths = downloader.download_all()
        
        print(f"\nDownloaded {len(paths)} videos")
        
        if args.youtube:
            print("\nDownloading YouTube samples...")
            youtube_paths = download_youtube_samples()
            paths.extend(youtube_paths)
        
        # Verify all downloads
        print("\nVerifying downloads...")
        results = downloader.verify_downloads()
        
        # Summary
        print("\nDownload Summary:")
        print("=" * 80)
        
        total_size = 0
        dialogue_videos = []
        
        for name, info in results.items():
            if info['exists'] and 'size_mb' in info:
                total_size += info['size_mb']
                if info.get('has_dialogue'):
                    dialogue_videos.append(name)
        
        print(f"Total videos: {len([r for r in results.values() if r['exists']])}")
        print(f"Total size: {total_size:.1f} MB")
        print(f"Videos with dialogue: {len(dialogue_videos)}")
        
        if dialogue_videos:
            print(f"Dialogue videos: {', '.join(dialogue_videos)}")
        
        # Create metadata file
        metadata_path = Path(args.output_dir) / 'video_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nMetadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()