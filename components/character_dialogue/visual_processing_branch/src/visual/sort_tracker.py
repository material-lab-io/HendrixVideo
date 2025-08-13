"""
SORT: Simple Online and Realtime Tracking

Implementation of the SORT algorithm for face tracking across video frames.
Based on the paper: "Simple Online and Realtime Tracking" by Bewley et al.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter
import logging

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """Represents a tracked face/person"""
    track_id: int
    kalman_filter: KalmanFilter
    time_since_update: int
    hits: int  # Total number of detections
    hit_streak: int  # Consecutive detections
    age: int  # Total frames since first detection
    embedding: Optional[np.ndarray] = None  # Face embedding for this track
    
    def predict(self):
        """Advance the kalman filter state and return predicted bounding box"""
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.kalman_filter.predict()
        self.age += 1
        return self.get_state()
    
    def update(self, bbox: np.ndarray, embedding: Optional[np.ndarray] = None):
        """Update the kalman filter with detected bbox"""
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        self.kalman_filter.update(convert_bbox_to_z(bbox))
        
        # Update embedding with exponential moving average
        if embedding is not None:
            if self.embedding is None:
                self.embedding = embedding
            else:
                # Weighted average: give more weight to recent embeddings
                alpha = 0.3  # Weight for new embedding
                self.embedding = (1 - alpha) * self.embedding + alpha * embedding
                # Normalize
                self.embedding = self.embedding / np.linalg.norm(self.embedding)
    
    def get_state(self) -> np.ndarray:
        """Get current bounding box estimate"""
        return convert_x_to_bbox(self.kalman_filter.x)[0]


def linear_assignment(cost_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve the linear assignment problem
    
    Returns:
        matched_indices: 2D array of matched track/detection indices
        unmatched_detections: 1D array of unmatched detection indices
        unmatched_tracks: 1D array of unmatched track indices
    """
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), np.arange(cost_matrix.shape[0]), np.empty((0,), dtype=int)
    
    matched_indices = linear_sum_assignment(cost_matrix)
    matched_indices = np.asarray(matched_indices).T
    
    unmatched_detections = []
    for d in range(cost_matrix.shape[0]):
        if d not in matched_indices[:, 0]:
            unmatched_detections.append(d)
    
    unmatched_tracks = []
    for t in range(cost_matrix.shape[1]):
        if t not in matched_indices[:, 1]:
            unmatched_tracks.append(t)
    
    # Filter out matched with high cost
    matches = []
    for m in matched_indices:
        if cost_matrix[m[0], m[1]] < 0.7:  # Cost threshold
            matches.append(m.reshape(1, 2))
        else:
            unmatched_detections.append(m[0])
            unmatched_tracks.append(m[1])
    
    if len(matches) == 0:
        matches = np.empty((0, 2), dtype=int)
    else:
        matches = np.concatenate(matches, axis=0)
    
    return matches, np.array(unmatched_detections), np.array(unmatched_tracks)


def iou_batch(bboxes1: np.ndarray, bboxes2: np.ndarray) -> np.ndarray:
    """Calculate IoU between two sets of bboxes
    
    Args:
        bboxes1: Array of bboxes (n, 4) in format [x1, y1, x2, y2]
        bboxes2: Array of bboxes (m, 4) in format [x1, y1, x2, y2]
    
    Returns:
        IoU matrix of shape (n, m)
    """
    bboxes1 = np.expand_dims(bboxes1, 1)
    bboxes2 = np.expand_dims(bboxes2, 0)
    
    xx1 = np.maximum(bboxes1[..., 0], bboxes2[..., 0])
    yy1 = np.maximum(bboxes1[..., 1], bboxes2[..., 1])
    xx2 = np.minimum(bboxes1[..., 2], bboxes2[..., 2])
    yy2 = np.minimum(bboxes1[..., 3], bboxes2[..., 3])
    
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    
    area1 = (bboxes1[..., 2] - bboxes1[..., 0]) * (bboxes1[..., 3] - bboxes1[..., 1])
    area2 = (bboxes2[..., 2] - bboxes2[..., 0]) * (bboxes2[..., 3] - bboxes2[..., 1])
    
    intersection = w * h
    union = area1 + area2 - intersection
    
    return intersection / union


def convert_bbox_to_z(bbox: np.ndarray) -> np.ndarray:
    """Convert bounding box to measurement for Kalman filter
    
    Takes [x1, y1, x2, y2] and returns [x, y, s, r] where:
    x, y is the center
    s is the scale (area)
    r is the aspect ratio
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.
    y = bbox[1] + h / 2.
    s = w * h  # scale is area
    r = w / float(h)
    return np.array([x, y, s, r]).reshape((4, 1))


def convert_x_to_bbox(x: np.ndarray, score: Optional[float] = None) -> np.ndarray:
    """Convert Kalman filter state to bounding box
    
    Takes [x, y, s, r] and returns [x1, y1, x2, y2]
    """
    w = np.sqrt(x[2] * x[3])
    h = x[2] / w
    if score is None:
        return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2.]).reshape((1, 4))
    else:
        return np.array([x[0] - w / 2., x[1] - h / 2., x[0] + w / 2., x[1] + h / 2., score]).reshape((1, 5))


class Sort:
    """Simple Online and Realtime Tracking"""
    
    def __init__(self, max_age: int = 30, min_hits: int = 3, 
                 iou_threshold: float = 0.3, use_embeddings: bool = True,
                 embedding_threshold: float = 0.6):
        """Initialize SORT tracker
        
        Args:
            max_age: Maximum frames to keep alive a track without detections
            min_hits: Minimum hits to start reporting a track
            iou_threshold: Minimum IoU for matching
            use_embeddings: Whether to use face embeddings for matching
            embedding_threshold: Minimum cosine similarity for embedding matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.use_embeddings = use_embeddings
        self.embedding_threshold = embedding_threshold
        self.tracks: List[Track] = []
        self.frame_count = 0
        self.next_id = 1
        
    def _init_kalman_filter(self, measurement: np.ndarray) -> KalmanFilter:
        """Initialize a Kalman filter for a new track"""
        kf = KalmanFilter(dim_x=7, dim_z=4)
        
        # State transition matrix (constant velocity model)
        kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement function
        kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        # Measurement uncertainty
        kf.R[2:, 2:] *= 10.
        
        # Process uncertainty
        kf.P[4:, 4:] *= 1000.  # High uncertainty for velocities
        kf.P *= 10.
        
        # Process noise
        kf.Q[-1, -1] *= 0.01
        kf.Q[4:, 4:] *= 0.01
        
        # Initialize state
        kf.x[:4] = measurement
        
        return kf
    
    def update(self, detections: np.ndarray, 
               embeddings: Optional[List[np.ndarray]] = None) -> np.ndarray:
        """Update tracks with new detections
        
        Args:
            detections: Array of detections, each row is [x1, y1, x2, y2, score]
            embeddings: Optional list of face embeddings corresponding to detections
            
        Returns:
            Array of tracks, each row is [x1, y1, x2, y2, track_id]
        """
        self.frame_count += 1
        
        # Get predictions from existing tracks
        trks = np.zeros((len(self.tracks), 5))
        to_del = []
        
        for t, trk in enumerate(trks):
            pos = self.tracks[t].predict()
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        
        # Remove invalid tracks
        for t in reversed(to_del):
            self.tracks.pop(t)
        
        # Associate detections to tracks
        matched, unmatched_dets, unmatched_trks = self.associate_detections_to_tracks(
            detections, trks, embeddings)
        
        # Update matched tracks
        for m in matched:
            embedding = embeddings[m[0]] if embeddings else None
            self.tracks[m[1]].update(detections[m[0], :4], embedding)
        
        # Create new tracks for unmatched detections
        for i in unmatched_dets:
            trk = self._create_track(detections[i, :4])
            if embeddings and i < len(embeddings):
                trk.embedding = embeddings[i]
            self.tracks.append(trk)
        
        # Prepare output
        ret = []
        for trk in self.tracks:
            d = trk.get_state()
            
            # Only report tracks that meet criteria
            if (trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append(np.concatenate((d, [trk.track_id])).reshape(1, -1))
            
            # Remove dead tracks
            if trk.time_since_update > self.max_age:
                self.tracks.remove(trk)
        
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))
    
    def associate_detections_to_tracks(self, detections: np.ndarray, 
                                     tracks: np.ndarray,
                                     embeddings: Optional[List[np.ndarray]] = None) -> Tuple:
        """Associate detections to existing tracks using IoU and optionally embeddings"""
        
        if len(tracks) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0,), dtype=int)
        
        # Calculate IoU cost matrix
        iou_matrix = iou_batch(detections[:, :4], tracks[:, :4])
        
        # Combine with embedding similarity if available
        if self.use_embeddings and embeddings is not None:
            embedding_matrix = self._calculate_embedding_similarity(embeddings)
            
            # Weighted combination of IoU and embedding similarity
            # Convert IoU to cost (1 - IoU)
            cost_matrix = 0.5 * (1 - iou_matrix) + 0.5 * (1 - embedding_matrix)
        else:
            cost_matrix = 1 - iou_matrix
        
        # Solve assignment problem
        return linear_assignment(cost_matrix)
    
    def _calculate_embedding_similarity(self, new_embeddings: List[np.ndarray]) -> np.ndarray:
        """Calculate cosine similarity between new embeddings and track embeddings"""
        n_dets = len(new_embeddings)
        n_trks = len(self.tracks)
        similarity_matrix = np.zeros((n_dets, n_trks))
        
        for d, det_emb in enumerate(new_embeddings):
            if det_emb is None:
                continue
                
            for t, trk in enumerate(self.tracks):
                if trk.embedding is None:
                    continue
                
                # Calculate cosine similarity
                det_emb_norm = det_emb / np.linalg.norm(det_emb)
                trk_emb_norm = trk.embedding / np.linalg.norm(trk.embedding)
                similarity = np.dot(det_emb_norm, trk_emb_norm)
                
                # Only consider if above threshold
                if similarity > self.embedding_threshold:
                    similarity_matrix[d, t] = similarity
        
        return similarity_matrix
    
    def _create_track(self, detection: np.ndarray) -> Track:
        """Create a new track from a detection"""
        kf = self._init_kalman_filter(convert_bbox_to_z(detection))
        track = Track(
            track_id=self.next_id,
            kalman_filter=kf,
            time_since_update=0,
            hits=1,
            hit_streak=1,
            age=1
        )
        self.next_id += 1
        return track