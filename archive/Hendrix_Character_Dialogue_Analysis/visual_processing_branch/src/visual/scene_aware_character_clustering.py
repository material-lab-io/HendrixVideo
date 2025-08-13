"""
Scene-aware character clustering module.
Groups and clusters characters considering scene boundaries and context.
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import json

from .scene_detector import SceneInfo, SceneDetector

logger = logging.getLogger(__name__)


class SceneCharacterCluster:
    """Represents a character cluster within a scene."""
    
    def __init__(self, cluster_id: str, scene_id: int):
        self.cluster_id = cluster_id
        self.scene_id = scene_id
        self.embeddings: List[np.ndarray] = []
        self.frame_numbers: List[int] = []
        self.timestamps: List[float] = []
        self.bounding_boxes: List[Tuple] = []
        self.representative_embedding: Optional[np.ndarray] = None
        
    def add_detection(self, embedding: np.ndarray, frame_num: int, 
                     timestamp: float, bbox: Tuple):
        """Add a face detection to this cluster."""
        self.embeddings.append(embedding)
        self.frame_numbers.append(frame_num)
        self.timestamps.append(timestamp)
        self.bounding_boxes.append(bbox)
        
    def compute_representative_embedding(self):
        """Compute the representative embedding as mean of all embeddings."""
        if self.embeddings:
            self.representative_embedding = np.mean(self.embeddings, axis=0)
            
    def get_temporal_span(self) -> Tuple[float, float]:
        """Get the time span of this cluster's appearances."""
        if self.timestamps:
            return min(self.timestamps), max(self.timestamps)
        return 0.0, 0.0


class SceneAwareCharacterClusterer:
    """Performs character clustering with scene awareness."""
    
    def __init__(self, 
                 intra_scene_threshold: float = 0.65,
                 inter_scene_threshold: float = 0.75,
                 min_cluster_size: int = 3,
                 use_dbscan: bool = True):
        """
        Initialize scene-aware clusterer.
        
        Args:
            intra_scene_threshold: Similarity threshold within scenes (lower = more strict)
            inter_scene_threshold: Similarity threshold across scenes (higher = more lenient)
            min_cluster_size: Minimum detections to form a cluster
            use_dbscan: Use DBSCAN (True) or Agglomerative clustering (False)
        """
        self.intra_scene_threshold = intra_scene_threshold
        self.inter_scene_threshold = inter_scene_threshold
        self.min_cluster_size = min_cluster_size
        self.use_dbscan = use_dbscan
        
        self.scene_clusters: Dict[int, List[SceneCharacterCluster]] = defaultdict(list)
        self.global_characters: List[Dict] = []
        
    def cluster_characters_by_scene(self, 
                                  character_data: List[Dict],
                                  scenes: List[SceneInfo]) -> Dict:
        """
        Cluster characters within each scene, then merge across scenes.
        
        Args:
            character_data: List of character detections from Schema C
            scenes: List of detected scenes
            
        Returns:
            Dictionary with clustering results
        """
        logger.info("Starting scene-aware character clustering")
        
        # Step 1: Group detections by scene
        scene_detections = self._group_detections_by_scene(character_data, scenes)
        
        # Step 2: Cluster within each scene
        for scene_id, detections in scene_detections.items():
            if detections:
                scene_clusters = self._cluster_within_scene(detections, scene_id)
                self.scene_clusters[scene_id] = scene_clusters
                
        logger.info(f"Created clusters for {len(self.scene_clusters)} scenes")
        
        # Step 3: Merge clusters across scenes
        self.global_characters = self._merge_across_scenes()
        
        logger.info(f"Merged into {len(self.global_characters)} global characters")
        
        # Step 4: Create enhanced character profiles
        enhanced_profiles = self._create_enhanced_profiles(character_data)
        
        return {
            'scene_clusters': self._serialize_scene_clusters(),
            'global_characters': self.global_characters,
            'enhanced_profiles': enhanced_profiles,
            'statistics': self._compute_statistics()
        }
    
    def _group_detections_by_scene(self, 
                                  character_data: List[Dict],
                                  scenes: List[SceneInfo]) -> Dict[int, List[Dict]]:
        """Group character detections by their scene."""
        scene_detections = defaultdict(list)
        
        for char in character_data:
            timestamp = char.get('first_appearance', 0.0)
            
            # Find which scene this detection belongs to
            scene_found = False
            for scene in scenes:
                if scene.contains_time(timestamp):
                    scene_detections[scene.scene_id].append(char)
                    scene_found = True
                    break
                    
            if not scene_found:
                # Detection outside any scene boundary
                logger.debug(f"Detection at {timestamp}s outside scene boundaries")
                
        return scene_detections
    
    def _cluster_within_scene(self, 
                            detections: List[Dict], 
                            scene_id: int) -> List[SceneCharacterCluster]:
        """Cluster character detections within a single scene."""
        if len(detections) < self.min_cluster_size:
            # Too few detections, create single cluster
            cluster = SceneCharacterCluster(f"scene{scene_id}_char0", scene_id)
            for det in detections:
                embedding = np.array(det['embedding'])
                cluster.add_detection(
                    embedding,
                    det.get('frame_number', 0),
                    det.get('first_appearance', 0.0),
                    det.get('bbox', (0, 0, 0, 0))
                )
            cluster.compute_representative_embedding()
            return [cluster]
        
        # Extract embeddings
        embeddings = np.array([det['embedding'] for det in detections])
        
        # Perform clustering
        if self.use_dbscan:
            # DBSCAN with cosine distance
            distances = 1 - cosine_similarity(embeddings)
            clustering = DBSCAN(
                eps=1 - self.intra_scene_threshold,
                min_samples=max(2, self.min_cluster_size // 2),
                metric='precomputed'
            ).fit(distances)
            labels = clustering.labels_
        else:
            # Agglomerative clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1 - self.intra_scene_threshold,
                metric='cosine',
                linkage='average'
            ).fit(embeddings)
            labels = clustering.labels_
        
        # Create cluster objects
        clusters = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1 and self.use_dbscan:
                continue  # Skip noise points
                
            cluster = SceneCharacterCluster(f"scene{scene_id}_char{label}", scene_id)
            
            # Add detections to cluster
            for i, det in enumerate(detections):
                if labels[i] == label:
                    cluster.add_detection(
                        embeddings[i],
                        det.get('frame_number', 0),
                        det.get('first_appearance', 0.0),
                        det.get('bbox', (0, 0, 0, 0))
                    )
                    
            cluster.compute_representative_embedding()
            clusters.append(cluster)
            
        logger.info(f"Scene {scene_id}: Created {len(clusters)} character clusters")
        return clusters
    
    def _merge_across_scenes(self) -> List[Dict]:
        """Merge character clusters across scenes to form global characters."""
        all_clusters = []
        for scene_clusters in self.scene_clusters.values():
            all_clusters.extend(scene_clusters)
            
        if not all_clusters:
            return []
            
        # Build similarity matrix between scene clusters
        n_clusters = len(all_clusters)
        similarity_matrix = np.zeros((n_clusters, n_clusters))
        
        for i in range(n_clusters):
            for j in range(i + 1, n_clusters):
                cluster_i = all_clusters[i]
                cluster_j = all_clusters[j]
                
                if (cluster_i.representative_embedding is not None and 
                    cluster_j.representative_embedding is not None):
                    
                    sim = cosine_similarity(
                        [cluster_i.representative_embedding],
                        [cluster_j.representative_embedding]
                    )[0, 0]
                    
                    similarity_matrix[i, j] = sim
                    similarity_matrix[j, i] = sim
                    
        # Greedy merging based on similarity
        merged_groups = []
        used_clusters = set()
        
        for i in range(n_clusters):
            if i in used_clusters:
                continue
                
            group = [i]
            used_clusters.add(i)
            
            # Find all clusters similar enough to merge
            for j in range(n_clusters):
                if j not in used_clusters and similarity_matrix[i, j] >= self.inter_scene_threshold:
                    group.append(j)
                    used_clusters.add(j)
                    
            merged_groups.append(group)
            
        # Create global character profiles
        global_characters = []
        
        for char_id, group in enumerate(merged_groups):
            character = {
                'character_id': f'char_{char_id}',
                'scene_clusters': [all_clusters[idx].cluster_id for idx in group],
                'scenes': list(set(all_clusters[idx].scene_id for idx in group)),
                'total_detections': sum(len(all_clusters[idx].embeddings) for idx in group),
                'embeddings': [],
                'temporal_span': self._compute_temporal_span(
                    [all_clusters[idx] for idx in group]
                )
            }
            
            # Collect all embeddings
            for idx in group:
                character['embeddings'].extend(all_clusters[idx].embeddings)
                
            # Compute global representative embedding
            if character['embeddings']:
                character['representative_embedding'] = np.mean(
                    character['embeddings'], axis=0
                ).tolist()
                
            global_characters.append(character)
            
        return global_characters
    
    def _compute_temporal_span(self, clusters: List[SceneCharacterCluster]) -> Dict:
        """Compute the temporal span across multiple clusters."""
        all_timestamps = []
        for cluster in clusters:
            all_timestamps.extend(cluster.timestamps)
            
        if all_timestamps:
            return {
                'start': min(all_timestamps),
                'end': max(all_timestamps),
                'duration': max(all_timestamps) - min(all_timestamps)
            }
        return {'start': 0, 'end': 0, 'duration': 0}
    
    def _create_enhanced_profiles(self, original_data: List[Dict]) -> List[Dict]:
        """Create enhanced character profiles with scene information."""
        enhanced_profiles = []
        
        for char in self.global_characters:
            profile = {
                'character_id': char['character_id'],
                'scenes': char['scenes'],
                'scene_appearances': defaultdict(int),
                'scene_confidence': {},
                'costume_variations': [],
                'temporal_consistency': self._compute_temporal_consistency(char),
                'cross_scene_similarity': self._compute_cross_scene_similarity(char)
            }
            
            # Count appearances per scene
            for scene_cluster_id in char['scene_clusters']:
                scene_id = int(scene_cluster_id.split('_')[0].replace('scene', ''))
                profile['scene_appearances'][scene_id] += 1
                
            # Compute per-scene confidence
            for scene_id in char['scenes']:
                profile['scene_confidence'][scene_id] = self._compute_scene_confidence(
                    char, scene_id
                )
                
            enhanced_profiles.append(profile)
            
        return enhanced_profiles
    
    def _compute_temporal_consistency(self, character: Dict) -> float:
        """Compute how consistently a character appears over time."""
        if not character.get('temporal_span'):
            return 0.0
            
        span = character['temporal_span']
        if span['duration'] == 0:
            return 0.0
            
        # Simple consistency: ratio of scenes appeared in vs total scenes in span
        return len(character['scenes']) / max(1, len(self.scene_clusters))
    
    def _compute_cross_scene_similarity(self, character: Dict) -> float:
        """Compute average similarity between character appearances across scenes."""
        if len(character['scenes']) < 2:
            return 1.0  # Single scene = perfect consistency
            
        # Get representative embeddings from each scene
        scene_embeddings = []
        for scene_id in character['scenes']:
            scene_clusters = self.scene_clusters.get(scene_id, [])
            for cluster in scene_clusters:
                if cluster.cluster_id in character['scene_clusters']:
                    if cluster.representative_embedding is not None:
                        scene_embeddings.append(cluster.representative_embedding)
                        
        if len(scene_embeddings) < 2:
            return 1.0
            
        # Compute pairwise similarities
        similarities = []
        for i in range(len(scene_embeddings)):
            for j in range(i + 1, len(scene_embeddings)):
                sim = cosine_similarity(
                    [scene_embeddings[i]], 
                    [scene_embeddings[j]]
                )[0, 0]
                similarities.append(sim)
                
        return np.mean(similarities) if similarities else 1.0
    
    def _compute_scene_confidence(self, character: Dict, scene_id: int) -> float:
        """Compute confidence score for character in specific scene."""
        scene_clusters = self.scene_clusters.get(scene_id, [])
        
        detections_in_scene = 0
        for cluster in scene_clusters:
            if cluster.cluster_id in character['scene_clusters']:
                detections_in_scene += len(cluster.embeddings)
                
        # Simple confidence based on detection count
        return min(1.0, detections_in_scene / 10.0)
    
    def _serialize_scene_clusters(self) -> Dict:
        """Serialize scene clusters for storage."""
        serialized = {}
        
        for scene_id, clusters in self.scene_clusters.items():
            serialized[scene_id] = []
            for cluster in clusters:
                serialized[scene_id].append({
                    'cluster_id': cluster.cluster_id,
                    'detection_count': len(cluster.embeddings),
                    'temporal_span': cluster.get_temporal_span(),
                    'representative_embedding': cluster.representative_embedding.tolist() 
                                              if cluster.representative_embedding is not None 
                                              else None
                })
                
        return serialized
    
    def _compute_statistics(self) -> Dict:
        """Compute clustering statistics."""
        total_clusters = sum(len(clusters) for clusters in self.scene_clusters.values())
        
        return {
            'total_scenes': len(self.scene_clusters),
            'total_scene_clusters': total_clusters,
            'avg_clusters_per_scene': total_clusters / max(1, len(self.scene_clusters)),
            'total_global_characters': len(self.global_characters),
            'reduction_ratio': total_clusters / max(1, len(self.global_characters))
        }