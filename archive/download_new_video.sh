#!/bin/bash

# Script to download new test video from Google Drive

echo "Downloading new test video from Google Drive..."

# Extract file ID from the URL
FILE_ID="1_AK0uehZHa5ljJnkAvIUlaJY064PHBm1"
OUTPUT_FILE="test_video_2.mp4"

# Method 1: Using wget with cookies
echo "Attempting download..."
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id='$FILE_ID -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$FILE_ID" -O $OUTPUT_FILE && rm -rf /tmp/cookies.txt

# Check if download was successful
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Download successful!"
    echo "Test video saved as: $OUTPUT_FILE"
    echo "File size: $(ls -lh $OUTPUT_FILE | awk '{print $5}')"
    
    # Verify the video file
    if command -v ffprobe &> /dev/null; then
        echo ""
        echo "Video information:"
        ffprobe -v quiet -print_format json -show_format -show_streams "$OUTPUT_FILE" | jq -r '.format | "Duration: \(.duration) seconds\nFormat: \(.format_name)\nSize: \(.size) bytes"' 2>/dev/null || echo "Could not read video metadata"
    fi
else
    echo "Method 1 failed. Trying alternative method..."
    
    # Method 2: Using gdown
    pip install gdown
    gdown "https://drive.google.com/uc?id=$FILE_ID" -O $OUTPUT_FILE
fi

echo ""
echo "Video downloaded as: $OUTPUT_FILE"