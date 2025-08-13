#!/usr/bin/env python3
"""
Test script for scene-aware character clustering
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.visual.scene_detector import SceneDetector
from src.visual.scene_aware_character_clustering import SceneAwareCharacterClusterer
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scene_detection(video_path: str):
    """Test scene detection on a video"""
    logger.info("Testing scene detection...")
    
    detector = SceneDetector(threshold=30.0, min_scene_len=15)
    scenes = detector.detect_scenes(video_path)
    
    logger.info(f"Detected {len(scenes)} scenes:")
    for scene in scenes[:5]:  # Show first 5 scenes
        logger.info(f"  Scene {scene.scene_id}: "
                   f"{scene.start_time:.2f}s - {scene.end_time:.2f}s "
                   f"(duration: {scene.duration:.2f}s)")
    
    if len(scenes) > 5:
        logger.info(f"  ... and {len(scenes) - 5} more scenes")
    
    # Test scene merging
    original_count = len(scenes)
    detector.merge_short_scenes(min_duration=2.0)
    logger.info(f"After merging short scenes: {original_count} -> {len(detector.scenes)} scenes")
    
    return detector


def test_scene_clustering():
    """Test scene-aware clustering with synthetic data"""
    logger.info("Testing scene-aware clustering with synthetic data...")
    
    # Create synthetic scenes
    scenes = [
        type('SceneInfo', (), {
            'scene_id': 0, 
            'start_time': 0.0, 
            'end_time': 10.0,
            'contains_time': lambda self, t: 0 <= t <= 10
        })(),
        type('SceneInfo', (), {
            'scene_id': 1,
            'start_time': 10.0,
            'end_time': 20.0,
            'contains_time': lambda self, t: 10 < t <= 20
        })()
    ]
    
    # Create synthetic character data
    # Character 1 appears in both scenes with similar embeddings
    char1_embedding_scene1 = np.random.randn(512)
    char1_embedding_scene2 = char1_embedding_scene1 + np.random.randn(512) * 0.1  # Small variation
    
    # Character 2 appears only in scene 1
    char2_embedding = np.random.randn(512)
    
    character_data = [
        # Character 1 in scene 1
        {'character_id': 'char_1', 'embedding': char1_embedding_scene1.tolist(),
         'frame_number': 100, 'first_appearance': 5.0, 'bbox': [0.1, 0.1, 0.3, 0.5]},
        {'character_id': 'char_1', 'embedding': (char1_embedding_scene1 + np.random.randn(512) * 0.05).tolist(),
         'frame_number': 150, 'first_appearance': 6.0, 'bbox': [0.1, 0.1, 0.3, 0.5]},
        
        # Character 2 in scene 1
        {'character_id': 'char_2', 'embedding': char2_embedding.tolist(),
         'frame_number': 200, 'first_appearance': 8.0, 'bbox': [0.6, 0.1, 0.8, 0.5]},
        
        # Character 1 in scene 2 (should be merged with scene 1 appearances)
        {'character_id': 'char_3', 'embedding': char1_embedding_scene2.tolist(),
         'frame_number': 400, 'first_appearance': 15.0, 'bbox': [0.2, 0.1, 0.4, 0.5]},
        {'character_id': 'char_3', 'embedding': (char1_embedding_scene2 + np.random.randn(512) * 0.05).tolist(),
         'frame_number': 450, 'first_appearance': 16.0, 'bbox': [0.2, 0.1, 0.4, 0.5]}
    ]
    
    # Test clustering
    clusterer = SceneAwareCharacterClusterer(
        intra_scene_threshold=0.65,
        inter_scene_threshold=0.75,
        min_cluster_size=2
    )
    
    results = clusterer.cluster_characters_by_scene(character_data, scenes)
    
    logger.info("Clustering results:")
    logger.info(f"  Scene clusters: {results['statistics']['total_scene_clusters']}")
    logger.info(f"  Global characters: {results['statistics']['total_global_characters']}")
    logger.info(f"  Reduction ratio: {results['statistics']['reduction_ratio']:.2f}")
    
    # Check if characters were properly merged
    expected_global_chars = 2  # char_1 from both scenes merged, char_2 separate
    actual_global_chars = len(results['global_characters'])
    
    if actual_global_chars == expected_global_chars:
        logger.info("✓ Characters correctly merged across scenes!")
    else:
        logger.warning(f"✗ Expected {expected_global_chars} global characters, "
                      f"got {actual_global_chars}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test scene-aware character clustering"
    )
    parser.add_argument(
        "--video",
        help="Optional video path for real scene detection test"
    )
    
    args = parser.parse_args()
    
    try:
        # Test synthetic clustering
        logger.info("="*50)
        logger.info("Testing synthetic scene-aware clustering")
        logger.info("="*50)
        clustering_results = test_scene_clustering()
        
        # Test real video scene detection if provided
        if args.video and os.path.exists(args.video):
            logger.info("\n" + "="*50)
            logger.info("Testing scene detection on real video")
            logger.info("="*50)
            scene_detector = test_scene_detection(args.video)
            
            logger.info("\nScene detection test completed successfully!")
        
        logger.info("\nAll tests completed!")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())