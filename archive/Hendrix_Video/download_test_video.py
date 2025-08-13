#!/usr/bin/env python3
"""Download a test video for the Hendrix Video Analysis pipeline."""

import os
import subprocess
import sys

def download_video(url, output_dir="test_videos", filename="test_video.mp4"):
    """Download a video using yt-dlp."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    # yt-dlp command with quality and duration filters
    cmd = [
        "venv/bin/yt-dlp",
        "-f", "best[height<=720]",  # Max 720p for reasonable file size
        "-o", output_path,
        "--no-playlist",  # Don't download playlists
        url
    ]
    
    print(f"Downloading video to: {output_path}")
    print("This may take a few minutes...")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Video downloaded successfully to: {output_path}")
        
        # Get video info
        info_cmd = ["ffprobe", "-v", "error", "-show_entries", 
                   "format=duration,size", "-of", "default=noprint_wrappers=1", 
                   output_path]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        print(f"\nVideo info:\n{result.stdout}")
        
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"✗ Error downloading video: {e}")
        return None

if __name__ == "__main__":
    # Creative Commons licensed videos suitable for testing
    # These are approximately 10 minutes long with varied shots
    test_videos = [
        # Big Buck Bunny (animated short film, ~10 min)
        "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
        # Sintel (animated short film, ~15 min)
        "https://www.youtube.com/watch?v=eRsGyueVLvQ",
        # Nature documentary style videos (if above don't work)
        "https://www.youtube.com/watch?v=LXb3EKWsInQ"  # Costa Rica in 4K
    ]
    
    # Try downloading the first available video
    for i, url in enumerate(test_videos):
        print(f"\nAttempting to download video {i+1}/{len(test_videos)}")
        output_path = download_video(url, filename=f"test_video_{i+1}.mp4")
        if output_path:
            print(f"\n✓ Successfully downloaded: {output_path}")
            print("\nYou can now run the analysis with:")
            print(f"  python src/main.py {output_path}")
            break
    else:
        print("\n✗ Failed to download any test videos")
        sys.exit(1)