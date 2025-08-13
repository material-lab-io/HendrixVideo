#!/bin/bash

# Script to download test video from Google Drive

echo "Downloading test video from Google Drive..."

# Extract file ID from the URL
FILE_ID="1j3Mqz4deLviZ8NPDLv6FKMDiKhYVkgff"
OUTPUT_FILE="test_video.mp4"

# Method 1: Using wget with cookies (works for most files)
echo "Attempting download method 1..."
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id='$FILE_ID -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$FILE_ID" -O $OUTPUT_FILE && rm -rf /tmp/cookies.txt

# Check if download was successful
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo "Download successful!"
    echo "Test video saved as: $OUTPUT_FILE"
    echo "File size: $(ls -lh $OUTPUT_FILE | awk '{print $5}')"
else
    echo "Method 1 failed. Trying alternative method..."
    
    # Method 2: Using gdown (Python package)
    echo "Installing gdown..."
    pip install gdown
    
    echo "Downloading with gdown..."
    gdown "https://drive.google.com/uc?id=$FILE_ID" -O $OUTPUT_FILE
    
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo "Download successful with gdown!"
        echo "Test video saved as: $OUTPUT_FILE"
        echo "File size: $(ls -lh $OUTPUT_FILE | awk '{print $5}')"
    else
        echo "Download failed. Please try one of these alternatives:"
        echo "1. Download manually from: https://drive.google.com/file/d/$FILE_ID/view"
        echo "2. Use a different test video"
        echo "3. Check if the file requires authentication"
        exit 1
    fi
fi

# Verify the video file
if command -v ffprobe &> /dev/null; then
    echo ""
    echo "Video information:"
    ffprobe -v quiet -print_format json -show_format -show_streams "$OUTPUT_FILE" | jq -r '.format | "Duration: \(.duration) seconds\nFormat: \(.format_name)\nSize: \(.size) bytes"' 2>/dev/null || echo "Could not read video metadata"
fi

echo ""
echo "To test the Hendrix pipeline with this video, run:"
echo "./test_hendrix_pipeline.sh $OUTPUT_FILE"
echo ""
echo "For quick testing (faster, lower quality):"
echo "./test_hendrix_pipeline.sh $OUTPUT_FILE --quick"