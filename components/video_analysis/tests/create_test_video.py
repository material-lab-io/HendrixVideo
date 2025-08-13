#!/usr/bin/env python3
"""
Create a simple test video for pipeline testing.
The video will have distinct shots with different colors/patterns.
"""

import cv2
import numpy as np
from pathlib import Path


def create_test_frame(width, height, color, text="", add_pattern=False):
    """Create a test frame with specified color and optional text/pattern."""
    # Create base frame with solid color
    frame = np.full((height, width, 3), color, dtype=np.uint8)
    
    # Add pattern if requested
    if add_pattern:
        # Add diagonal lines
        for i in range(0, width, 20):
            cv2.line(frame, (i, 0), (i + height, height), (255, 255, 255), 2)
    
    # Add text if provided
    if text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 2, 3)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        # Add text shadow
        cv2.putText(frame, text, (text_x + 2, text_y + 2), font, 2, (0, 0, 0), 3)
        # Add text
        cv2.putText(frame, text, (text_x, text_y), font, 2, (255, 255, 255), 3)
    
    return frame


def create_transition_frames(frame1, frame2, num_frames, transition_type='cut'):
    """Create transition frames between two frames."""
    frames = []
    
    if transition_type == 'cut':
        # Hard cut - no transition frames
        return frames
    
    elif transition_type == 'dissolve':
        # Gradual dissolve between frames
        for i in range(num_frames):
            alpha = i / (num_frames - 1)
            blended = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
            frames.append(blended)
    
    elif transition_type == 'fade':
        # Fade to black then to new frame
        black_frame = np.zeros_like(frame1)
        half = num_frames // 2
        
        # Fade out
        for i in range(half):
            alpha = 1 - (i / half)
            blended = cv2.addWeighted(frame1, alpha, black_frame, 1 - alpha, 0)
            frames.append(blended)
        
        # Fade in
        for i in range(half, num_frames):
            alpha = (i - half) / (num_frames - half)
            blended = cv2.addWeighted(black_frame, 1 - alpha, frame2, alpha, 0)
            frames.append(blended)
    
    return frames


def create_test_video(output_path='test_video.mp4', width=640, height=480, fps=30):
    """Create a test video with multiple shots and transitions."""
    # Define video codec and create VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Define shots with different characteristics
    shots = [
        {
            'duration': 3.0,  # seconds
            'color': (180, 100, 100),  # BGR - Light blue
            'text': 'Shot 1: Opening',
            'pattern': False
        },
        {
            'duration': 2.5,
            'color': (100, 180, 100),  # Light green
            'text': 'Shot 2: Action',
            'pattern': True
        },
        {
            'duration': 4.0,
            'color': (100, 100, 180),  # Light red
            'text': 'Shot 3: Dialog',
            'pattern': False
        },
        {
            'duration': 2.0,
            'color': (150, 150, 150),  # Gray
            'text': 'Shot 4: Transition',
            'pattern': True
        },
        {
            'duration': 3.5,
            'color': (200, 150, 100),  # Light orange
            'text': 'Shot 5: Conclusion',
            'pattern': False
        }
    ]
    
    # Define transitions between shots
    transitions = ['cut', 'dissolve', 'cut', 'fade']
    
    print(f"Creating test video: {output_path}")
    print(f"Resolution: {width}x{height}, FPS: {fps}")
    
    total_frames = 0
    
    for i, shot in enumerate(shots):
        # Create base frame for this shot
        base_frame = create_test_frame(
            width, height, 
            shot['color'], 
            shot['text'], 
            shot['pattern']
        )
        
        # Calculate number of frames for this shot
        num_frames = int(shot['duration'] * fps)
        
        # Add slight variations to make frames different
        for frame_idx in range(num_frames):
            # Create frame with slight variation
            frame = base_frame.copy()
            
            # Add frame counter
            counter_text = f"Frame: {total_frames + frame_idx}"
            cv2.putText(frame, counter_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add timestamp
            timestamp = (total_frames + frame_idx) / fps
            time_text = f"Time: {timestamp:.2f}s"
            cv2.putText(frame, time_text, (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Write frame
            out.write(frame)
        
        total_frames += num_frames
        
        # Add transition if not the last shot
        if i < len(shots) - 1:
            transition_type = transitions[i] if i < len(transitions) else 'cut'
            
            if transition_type != 'cut':
                # Create next frame for transition
                next_frame = create_test_frame(
                    width, height,
                    shots[i + 1]['color'],
                    shots[i + 1]['text'],
                    shots[i + 1]['pattern']
                )
                
                # Create transition frames
                transition_frames = create_transition_frames(
                    base_frame, next_frame, 
                    int(0.5 * fps),  # 0.5 second transitions
                    transition_type
                )
                
                for t_frame in transition_frames:
                    out.write(t_frame)
                    total_frames += 1
        
        print(f"  Shot {i+1}: {num_frames} frames ({shot['duration']}s)")
    
    # Release everything
    out.release()
    cv2.destroyAllWindows()
    
    total_duration = total_frames / fps
    print(f"\nVideo created successfully!")
    print(f"Total frames: {total_frames}")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Output file: {output_path}")
    
    return output_path, total_frames, total_duration


if __name__ == "__main__":
    # Create test video in the tests directory
    output_path = Path(__file__).parent / "sample_video.mp4"
    create_test_video(str(output_path))