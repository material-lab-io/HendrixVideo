#!/usr/bin/env python3
"""
Adaptive Character-Dialogue Pipeline

This script runs an enhanced pipeline with adaptive frame extraction
based on dialogue timing for improved character-dialogue matching.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import argparse
import logging
import subprocess
import json
import time
from datetime import datetime
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdaptivePipeline:
    """Enhanced pipeline with adaptive frame extraction"""
    
    def __init__(self, output_base_dir: str = "output/adaptive_pipeline"):
        self.output_base_dir = Path(output_base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_base_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def run_audio_pipeline(self, video_path: str, whisper_model: str = "base") -> Path:
        """Run audio processing pipeline"""
        logger.info("="*60)
        logger.info("STAGE 1: AUDIO PROCESSING")
        logger.info("="*60)
        
        audio_script = Path("../audio_processing_branch/scripts/complete_audio_pipeline.py").resolve()
        abs_video_path = Path(video_path).resolve()
        audio_output_dir = self.session_dir / "audio_output"
        
        cmd = [
            sys.executable,
            str(audio_script),
            str(abs_video_path),
            "--whisper-model", whisper_model,
            "--output", str(audio_output_dir)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find output directory
            audio_outputs = [d for d in audio_output_dir.glob("*") if d.is_dir()]
            if not audio_outputs:
                raise RuntimeError("No audio output directory found")
            
            audio_output_path = audio_outputs[0]
            logger.info(f"Audio processing complete. Output: {audio_output_path}")
            
            # Verify Schema A exists
            schema_a = audio_output_path / "schemas" / "schema_a_transcription.json"
            if not schema_a.exists():
                raise RuntimeError(f"Schema A not found")
                
            return audio_output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio pipeline failed: {e.stderr}")
            raise
    
    def run_adaptive_visual_pipeline(self, 
                                   video_path: str, 
                                   schema_a_path: Path,
                                   min_confidence: float = 0.5) -> Path:
        """Run visual processing with adaptive frame extraction"""
        logger.info("="*60)
        logger.info("STAGE 2: ADAPTIVE VISUAL PROCESSING")
        logger.info("="*60)
        
        visual_output_dir = self.session_dir / "visual_output"
        visual_output_dir.mkdir(exist_ok=True)
        
        # Import required modules
        from src.visual.adaptive_frame_extractor import (
            AdaptiveFrameExtractor, 
            AdaptiveExtractionConfig,
            create_dialogue_segments_from_schema_a
        )
        from tracked_visual_pipeline import TrackedVisualPipeline
        
        try:
            # Analyze video characteristics
            logger.info("Analyzing video characteristics...")
            extractor = AdaptiveFrameExtractor()
            video_analysis = extractor.analyze_video_characteristics(video_path)
            
            logger.info(f"Video duration: {video_analysis['video_properties']['duration']:.1f}s")
            logger.info(f"Average quality: {video_analysis['quality_analysis']['average_quality']:.2f}")
            
            # Create dialogue segments from Schema A
            dialogue_segments = create_dialogue_segments_from_schema_a(str(schema_a_path))
            logger.info(f"Found {len(dialogue_segments)} dialogue segments")
            
            # Configure adaptive extraction
            config = AdaptiveExtractionConfig(
                base_fps=video_analysis['recommendations']['base_fps'],
                dialogue_fps=video_analysis['recommendations']['dialogue_fps'],
                quality_threshold=video_analysis['recommendations']['quality_threshold'],
                total_frame_budget=video_analysis['recommendations']['total_frame_budget']
            )
            
            # Extract frames adaptively
            logger.info("Extracting frames based on dialogue timing...")
            frames_dir = visual_output_dir / "extracted_frames"
            frames = extractor.extract_frames_with_dialogue(
                video_path,
                dialogue_segments,
                str(frames_dir)
            )
            
            logger.info(f"Extracted {len(frames)} frames adaptively")
            
            # Run face detection and tracking on extracted frames
            logger.info("Running face detection and tracking...")
            pipeline = TrackedVisualPipeline(
                output_dir=str(visual_output_dir),
                device='cpu',
                min_appearances=2  # Lower threshold for adaptive extraction
            )
            
            # Process pre-extracted frames
            schema_c = pipeline.process_extracted_frames(
                frames,
                video_path=video_path,
                fps=video_analysis['video_properties']['fps']
            )
            
            logger.info(f"Visual processing complete. Characters found: {len(schema_c.characters)}")
            
            # Save extraction metadata
            metadata_path = visual_output_dir / "extraction_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump({
                    'video_analysis': video_analysis,
                    'extraction_config': config.to_dict(),
                    'frames_extracted': len(frames),
                    'dialogue_segments': len(dialogue_segments)
                }, f, indent=2)
            
            return visual_output_dir
            
        except Exception as e:
            logger.error(f"Visual pipeline failed: {e}")
            raise
    
    def run_enhanced_fusion(self, 
                          audio_dir: Path, 
                          visual_dir: Path,
                          adaptive_matching: bool = True) -> Path:
        """Run fusion with enhanced matching strategies"""
        logger.info("="*60)
        logger.info("STAGE 3: ENHANCED CHARACTER-DIALOGUE FUSION")
        logger.info("="*60)
        
        fusion_output_dir = self.session_dir / "fusion_output"
        
        # Import required modules
        sys.path.append(str(Path(__file__).parent.parent))
        from src.fusion.character_dialogue_matcher import CharacterDialogueMatcher, FusionConfig
        from src.fusion.heuristic_matcher import HeuristicConfig
        from src.schemas import SchemaA, SchemaB, SchemaC, SchemaD
        from src.schemas import TranscriptionSegment, SpeakerSegment
        
        try:
            # Load schemas
            logger.info("Loading schemas...")
            
            # Load Schema A
            schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
            with open(schema_a_path, 'r') as f:
                schema_a_data = json.load(f)
            
            schema_a = SchemaA(
                video_id=schema_a_data['video_id'],
                duration=schema_a_data['duration']
            )
            for seg in schema_a_data['segments']:
                schema_a.add_segment(TranscriptionSegment(
                    segment_id=seg['segment_id'],
                    text=seg['text'],
                    start_time=seg['start_time'],
                    end_time=seg['end_time'],
                    confidence=seg['confidence'],
                    emotion=seg.get('emotion'),
                    emotion_confidence=seg.get('emotion_confidence')
                ))
            
            # Load Schema B if available
            schema_b_path = audio_dir / "schemas" / "schema_b_speakers.json"
            schema_b = None
            if schema_b_path.exists():
                with open(schema_b_path, 'r') as f:
                    schema_b_data = json.load(f)
                
                schema_b = SchemaB(
                    video_id=schema_b_data['video_id'],
                    duration=schema_b_data['duration'],
                    num_speakers=schema_b_data['num_speakers']
                )
                for seg in schema_b_data['segments']:
                    schema_b.add_segment(SpeakerSegment(
                        segment_id=seg['segment_id'],
                        speaker_id=seg['speaker_id'],
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        confidence=seg.get('confidence', 1.0)
                    ))
            
            # Load Schema C
            schema_c_path = visual_dir / "character_data_schemaC.json"
            with open(schema_c_path, 'r') as f:
                schema_c_data = json.load(f)
            
            from src.schemas import CharacterInfo
            schema_c = SchemaC(
                video_id=schema_c_data['video_id'],
                duration=schema_c_data['duration'],
                fps=schema_c_data['fps'],
                total_frames=schema_c_data['total_frames'],
                metadata=schema_c_data.get('metadata', {}),
                created_at=schema_c_data.get('created_at')
            )
            
            for char_id, char_data in schema_c_data.get('characters', {}).items():
                character = CharacterInfo(**char_data)
                schema_c.add_character(character)
            
            # Configure adaptive matching if enabled
            if adaptive_matching:
                # Calculate optimal window based on character detection density
                total_detections = len(schema_c.detections) if hasattr(schema_c, 'detections') else 0
                detection_density = total_detections / schema_c.duration if schema_c.duration > 0 else 0
                
                # Adaptive window sizing
                if detection_density < 0.1:  # Sparse detections
                    window_extension = 60.0  # Very large window
                elif detection_density < 0.5:
                    window_extension = 30.0  # Large window
                elif detection_density < 1.0:
                    window_extension = 10.0  # Medium window
                else:
                    window_extension = 5.0   # Small window
                
                logger.info(f"Detection density: {detection_density:.2f} detections/s")
                logger.info(f"Using adaptive window: ±{window_extension}s")
                
                heuristic_config = HeuristicConfig(
                    window_extension=window_extension,
                    temporal_window=min(2.0, window_extension / 10),
                    single_character_weight=0.8,
                    temporal_proximity_weight=0.6
                )
            else:
                heuristic_config = HeuristicConfig()
            
            # Create matcher with enhanced config
            config = FusionConfig(
                use_llm=False,
                heuristic_weight=1.0,
                llm_weight=0.0,
                min_confidence_threshold=0.25,  # Lower threshold for adaptive matching
                heuristic_config=heuristic_config
            )
            
            matcher = CharacterDialogueMatcher(config=config)
            schema_d = matcher.match_schemas(
                schema_a=schema_a,
                schema_c=schema_c,
                schema_b=schema_b
            )
            
            # Save results
            fusion_output_dir.mkdir(exist_ok=True)
            schema_d_path = fusion_output_dir / "schema_d_matches.json"
            schema_d.save_json(str(schema_d_path))
            
            # Generate detailed report
            self._generate_adaptive_report(schema_d, fusion_output_dir, adaptive_matching)
            
            logger.info(f"Fusion complete. Matches: {len(schema_d.matches)}/{len(schema_a.segments)}")
            
            return fusion_output_dir
            
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            raise
    
    def _generate_adaptive_report(self, schema_d, output_dir: Path, adaptive: bool):
        """Generate detailed report for adaptive pipeline"""
        report_path = output_dir / "adaptive_fusion_report.md"
        
        matched = len(schema_d.matches)
        total = len(schema_d.matches) + len(schema_d.unmatched_dialogues)
        
        with open(report_path, 'w') as f:
            f.write(f"# Adaptive Character-Dialogue Fusion Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Video ID:** {schema_d.video_id}\n")
            f.write(f"**Adaptive Matching:** {'Enabled' if adaptive else 'Disabled'}\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- Total dialogues: {total}\n")
            f.write(f"- Matched: {matched} ({matched/total*100:.1f}%)\n")
            f.write(f"- Unmatched: {len(schema_d.unmatched_dialogues)}\n\n")
            
            if matched > 0:
                # Confidence distribution
                confidences = [m.matching_score.final_score for m in schema_d.matches 
                             if m.matching_score]
                if confidences:
                    f.write(f"## Confidence Distribution\n")
                    f.write(f"- Average: {sum(confidences)/len(confidences):.3f}\n")
                    f.write(f"- Min: {min(confidences):.3f}\n")
                    f.write(f"- Max: {max(confidences):.3f}\n\n")
            
            f.write(f"## Matches by Character\n")
            char_counts = {}
            for match in schema_d.matches:
                char_id = match.character_id
                char_counts[char_id] = char_counts.get(char_id, 0) + 1
            
            for char_id, count in sorted(char_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- Character {char_id}: {count} dialogues\n")
            
            f.write(f"\n## Detailed Matches\n")
            for i, match in enumerate(schema_d.matches[:20]):  # First 20 matches
                dialogue = match.dialogue_segment
                f.write(f"\n### Match {i+1}\n")
                f.write(f"- Character: {match.character_id}\n")
                f.write(f"- Text: \"{dialogue.text}\"\n")
                f.write(f"- Time: {dialogue.start_time:.1f}s - {dialogue.end_time:.1f}s\n")
                if dialogue.emotion:
                    f.write(f"- Emotion: {dialogue.emotion} ({dialogue.emotion_confidence:.2f})\n")
                if match.matching_score:
                    f.write(f"- Confidence: {match.matching_score.final_score:.3f}\n")
                    if match.matching_score.heuristic_scores:
                        f.write(f"- Heuristic scores: {match.matching_score.heuristic_scores}\n")
    
    def run_complete_adaptive_pipeline(self, 
                                     video_path: str, 
                                     whisper_model: str = "base",
                                     adaptive_matching: bool = True) -> dict:
        """Run the complete adaptive pipeline"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("ADAPTIVE CHARACTER-DIALOGUE ANALYSIS PIPELINE")
        logger.info("="*60)
        logger.info(f"Video: {video_path}")
        logger.info(f"Session: {self.session_dir}")
        logger.info("="*60)
        
        results = {
            'video': video_path,
            'session_dir': str(self.session_dir),
            'success': False,
            'error': None,
            'timings': {}
        }
        
        try:
            # Stage 1: Audio
            audio_start = time.time()
            audio_dir = self.run_audio_pipeline(video_path, whisper_model)
            results['timings']['audio'] = time.time() - audio_start
            results['audio_dir'] = str(audio_dir)
            
            # Stage 2: Adaptive Visual
            visual_start = time.time()
            schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
            visual_dir = self.run_adaptive_visual_pipeline(video_path, schema_a_path)
            results['timings']['visual'] = time.time() - visual_start
            results['visual_dir'] = str(visual_dir)
            
            # Stage 3: Enhanced Fusion
            fusion_start = time.time()
            fusion_dir = self.run_enhanced_fusion(audio_dir, visual_dir, adaptive_matching)
            results['timings']['fusion'] = time.time() - fusion_start
            results['fusion_dir'] = str(fusion_dir)
            
            # Overall stats
            results['timings']['total'] = time.time() - start_time
            results['success'] = True
            
            # Generate final report
            self._generate_final_report(results)
            
            logger.info("="*60)
            logger.info("ADAPTIVE PIPELINE COMPLETE!")
            logger.info(f"Total time: {results['timings']['total']:.1f}s")
            logger.info(f"Results: {self.session_dir}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['error'] = str(e)
            results['timings']['total'] = time.time() - start_time
            
        return results
    
    def _generate_final_report(self, results):
        """Generate comprehensive final report"""
        report_path = self.session_dir / "ADAPTIVE_PIPELINE_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Adaptive Pipeline Report\n\n")
            f.write(f"**Session:** {self.timestamp}\n")
            f.write(f"**Video:** {results['video']}\n")
            f.write(f"**Status:** {'Success' if results['success'] else 'Failed'}\n\n")
            
            f.write("## Processing Times\n")
            for stage, duration in results['timings'].items():
                f.write(f"- {stage.capitalize()}: {duration:.1f}s\n")
            
            f.write("\n## Output Locations\n")
            f.write(f"- Audio: {results.get('audio_dir', 'N/A')}\n")
            f.write(f"- Visual: {results.get('visual_dir', 'N/A')}\n")
            f.write(f"- Fusion: {results.get('fusion_dir', 'N/A')}\n")
            
            if results.get('error'):
                f.write(f"\n## Error\n{results['error']}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run adaptive character-dialogue analysis pipeline"
    )
    parser.add_argument('video_path', help='Path to input video file')
    parser.add_argument('--output', default='output/adaptive_pipeline',
                       help='Base output directory')
    parser.add_argument('--whisper-model', default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                       help='Whisper model size')
    parser.add_argument('--no-adaptive', action='store_true',
                       help='Disable adaptive matching')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AdaptivePipeline(args.output)
    
    # Run pipeline
    results = pipeline.run_complete_adaptive_pipeline(
        args.video_path,
        args.whisper_model,
        adaptive_matching=not args.no_adaptive
    )
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    sys.exit(main())