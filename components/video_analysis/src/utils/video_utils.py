import cv2
import numpy as np
from typing import List, Tuple, Optional, Generator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Utility class for video processing operations."""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def release(self):
        """Release video capture resources."""
        if self.cap:
            self.cap.release()
    
    def get_frame_at_time(self, time_seconds: float) -> Optional[np.ndarray]:
        """Extract a single frame at the specified time."""
        frame_number = int(time_seconds * self.fps)
        return self.get_frame_at_index(frame_number)
    
    def get_frame_at_index(self, frame_index: int) -> Optional[np.ndarray]:
        """Extract a single frame at the specified index."""
        if frame_index < 0 or frame_index >= self.frame_count:
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        if ret:
            return frame
        return None
    
    def extract_keyframe(self, start_time: float, end_time: float, 
                        method: str = "middle") -> Optional[np.ndarray]:
        """Extract a keyframe from a shot based on the specified method."""
        if method == "middle":
            keyframe_time = (start_time + end_time) / 2
        elif method == "first":
            keyframe_time = start_time + 0.1  # Slight offset to avoid transition frames
        elif method == "last":
            keyframe_time = end_time - 0.1
        else:
            raise ValueError(f"Unknown keyframe extraction method: {method}")
        
        return self.get_frame_at_time(keyframe_time)
    
    def save_frame(self, frame: np.ndarray, output_path: str, 
                   quality: int = 95) -> bool:
        """Save a frame as an image file."""
        try:
            if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(output_path, frame)
            return True
        except Exception as e:
            logger.error(f"Failed to save frame: {e}")
            return False
    
    def frames_generator(self, start_frame: int = 0, 
                        end_frame: Optional[int] = None,
                        step: int = 1) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Generate frames from the video with optional range and step."""
        if end_frame is None:
            end_frame = self.frame_count
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        for frame_idx in range(start_frame, end_frame, step):
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame_idx, frame
            
            # Skip frames if step > 1
            for _ in range(step - 1):
                self.cap.read()
    
    def get_video_metadata(self) -> dict:
        """Get comprehensive video metadata."""
        fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        
        return {
            "filename": Path(self.video_path).name,
            "duration": self.duration,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "total_frames": self.frame_count,
            "codec": codec,
            "format": Path(self.video_path).suffix[1:]  # Remove the dot
        }


def calculate_frame_difference(frame1: np.ndarray, frame2: np.ndarray, 
                             method: str = "mse") -> float:
    """Calculate the difference between two frames."""
    if frame1.shape != frame2.shape:
        raise ValueError("Frames must have the same dimensions")
    
    if method == "mse":
        # Mean Squared Error
        diff = np.mean((frame1.astype(float) - frame2.astype(float)) ** 2)
    elif method == "histogram":
        # Histogram comparison
        hist1 = cv2.calcHist([frame1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([frame2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        diff = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CHISQR)
    else:
        raise ValueError(f"Unknown difference method: {method}")
    
    return diff


def resize_frame_aspect_ratio(frame: np.ndarray, max_width: int, 
                            max_height: int) -> np.ndarray:
    """Resize frame while maintaining aspect ratio."""
    height, width = frame.shape[:2]
    
    # Calculate scaling factor
    scale = min(max_width / width, max_height / height)
    
    if scale < 1:
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return frame