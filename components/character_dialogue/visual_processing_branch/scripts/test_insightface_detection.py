#!/usr/bin/env python3
"""
Test InsightFace detection directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from insightface.app import FaceAnalysis

def test_insightface():
    print("Testing InsightFace detection...")
    
    # Initialize FaceAnalysis
    app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    
    # Load test video
    video_path = '../test_video.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return
    
    # Read frames and detect faces
    faces_found = 0
    frames_checked = 0
    
    for i in range(10):  # Check first 10 frames
        ret, frame = cap.read()
        if not ret:
            break
            
        frames_checked += 1
        
        # Detect faces
        faces = app.get(frame)
        
        if faces:
            faces_found += 1
            print(f"Frame {i}: Found {len(faces)} faces")
            
            # Save frame with detections
            for face in faces:
                bbox = face.bbox.astype(int)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                
            cv2.imwrite(f'test_detection_frame_{i}.jpg', frame)
        else:
            print(f"Frame {i}: No faces found")
    
    cap.release()
    
    print(f"\nSummary: Found faces in {faces_found}/{frames_checked} frames")

if __name__ == "__main__":
    test_insightface()