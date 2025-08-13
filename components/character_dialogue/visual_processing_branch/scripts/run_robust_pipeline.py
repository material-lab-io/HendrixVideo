#!/usr/bin/env python3
"""
Robust Character-Dialogue Pipeline

This is the ultimate pipeline that works with any video by:
- Using multi-level frame extraction with fallback strategies
- Implementing character continuity tracking
- Auto-calibrating confidence thresholds
- Performing intelligent gap-filling
- Learning from matches progressively
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
import numpy as np
from typing import Dict, List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RobustPipeline:
    """The ultimate robust pipeline for any video"""
    
    def __init__(self, output_base_dir: str = "output/robust_pipeline"):
        self.output_base_dir = Path(output_base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_base_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.performance_metrics = {}
        
    def run_audio_pipeline(self, video_path: str, whisper_model: str = "base") -> Path:
        """Run audio processing with automatic model selection"""
        logger.info("="*60)
        logger.info("STAGE 1: AUDIO PROCESSING")
        logger.info("="*60)
        
        # First, analyze video to choose best Whisper model
        video_duration = self._get_video_duration(video_path)
        
        # Auto-select Whisper model based on duration
        if whisper_model == "auto":
            if video_duration < 300:  # < 5 minutes
                whisper_model = "base"
            elif video_duration < 1800:  # < 30 minutes
                whisper_model = "small"
            else:
                whisper_model = "base"  # Balance speed and quality
            logger.info(f"Auto-selected Whisper model: {whisper_model}")
        
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
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            audio_time = time.time() - start_time
            self.performance_metrics['audio_processing_time'] = audio_time
            
            # Find output directory
            audio_outputs = [d for d in audio_output_dir.glob("*") if d.is_dir()]
            if not audio_outputs:
                raise RuntimeError("No audio output directory found")
            
            audio_output_path = audio_outputs[0]
            logger.info(f"Audio processing complete in {audio_time:.1f}s")
            
            # Check for hallucinations and quality issues
            self._validate_audio_output(audio_output_path)
            
            return audio_output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio pipeline failed: {e.stderr}")
            raise
    
    def run_robust_visual_pipeline(self, 
                                 video_path: str, 
                                 schema_a_path: Path) -> Path:
        """Run visual processing with robust frame extraction"""
        logger.info("="*60)
        logger.info("STAGE 2: ROBUST VISUAL PROCESSING")
        logger.info("="*60)
        
        visual_output_dir = self.session_dir / "visual_output"
        visual_output_dir.mkdir(exist_ok=True)
        
        # Import required modules
        from src.visual.robust_frame_extractor import RobustFrameExtractor, ExtractionResult
        from src.visual.adaptive_frame_extractor import create_dialogue_segments_from_schema_a
        from tracked_visual_pipeline import TrackedVisualPipeline
        
        try:
            start_time = time.time()
            
            # Create dialogue segments
            dialogue_segments = create_dialogue_segments_from_schema_a(str(schema_a_path))
            logger.info(f"Processing {len(dialogue_segments)} dialogue segments")
            
            # Use robust frame extraction
            extractor = RobustFrameExtractor(
                target_coverage=0.8,  # Aim for 80% temporal coverage
                min_frames=max(100, len(dialogue_segments) * 5)  # At least 5 frames per dialogue
            )
            
            # Extract frames with multi-level fallback
            frames_dir = visual_output_dir / "extracted_frames"
            extraction_result = extractor.extract_frames_adaptive(
                video_path,
                [{'start_time': s.start_time, 'end_time': s.end_time} for s in dialogue_segments],
                str(frames_dir)
            )
            
            logger.info(f"Extracted {len(extraction_result.frames)} frames using {extraction_result.strategy_used}")
            logger.info(f"Coverage: {extraction_result.coverage_stats['temporal_coverage']:.1%}")
            
            # Save extraction stats
            with open(visual_output_dir / "extraction_stats.json", 'w') as f:
                json.dump({
                    'strategy_used': extraction_result.strategy_used,
                    'frames_extracted': len(extraction_result.frames),
                    'quality_stats': extraction_result.quality_stats,
                    'coverage_stats': extraction_result.coverage_stats
                }, f, indent=2)
            
            # Run face detection and tracking
            logger.info("Running face detection and tracking...")
            pipeline = TrackedVisualPipeline(
                output_dir=str(visual_output_dir),
                device='cuda' if self._check_cuda() else 'cpu',
                min_appearances=1  # Very low threshold for robust detection
            )
            
            # Get video properties
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
            # Process extracted frames
            schema_c = pipeline.process_extracted_frames(
                extraction_result.frames,
                video_path=video_path,
                fps=fps
            )
            
            # Check if we need gap filling
            if len(schema_c.characters) < 2 or extraction_result.coverage_stats['dialogue_coverage'] < 0.7:
                logger.info("Performing gap-filling extraction...")
                gaps = self._identify_temporal_gaps(
                    extraction_result.frames, 
                    dialogue_segments,
                    schema_c
                )
                
                if gaps:
                    additional_frames = extractor.extract_gap_filling_frames(
                        video_path,
                        extraction_result.frames,
                        gaps,
                        frames_per_gap=10
                    )
                    
                    if additional_frames:
                        logger.info(f"Extracted {len(additional_frames)} gap-filling frames")
                        
                        # Process additional frames
                        schema_c_additional = pipeline.process_extracted_frames(
                            additional_frames,
                            video_path=video_path,
                            fps=fps
                        )
                        
                        # Merge results
                        schema_c = self._merge_schemas(schema_c, schema_c_additional)
            
            visual_time = time.time() - start_time
            self.performance_metrics['visual_processing_time'] = visual_time
            
            logger.info(f"Visual processing complete in {visual_time:.1f}s")
            logger.info(f"Found {len(schema_c.characters)} characters")
            
            return visual_output_dir
            
        except Exception as e:
            logger.error(f"Visual pipeline failed: {e}")
            raise
    
    def run_advanced_fusion(self, 
                          audio_dir: Path, 
                          visual_dir: Path) -> Path:
        """Run advanced fusion with all improvements"""
        logger.info("="*60)
        logger.info("STAGE 3: ADVANCED CHARACTER-DIALOGUE FUSION")
        logger.info("="*60)
        
        fusion_output_dir = self.session_dir / "fusion_output"
        fusion_output_dir.mkdir(exist_ok=True)
        
        # Import required modules
        sys.path.append(str(Path(__file__).parent.parent))
        from src.fusion.advanced_character_matcher import AdvancedCharacterMatcher
        from src.schemas import SchemaA, SchemaB, SchemaC, SchemaD
        from src.schemas import TranscriptionSegment, SpeakerSegment
        
        try:
            start_time = time.time()
            
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
            
            # Create SchemaC with all data
            from src.schemas import CharacterInfo, FaceDetection
            schema_c = SchemaC(
                video_id=schema_c_data['video_id'],
                duration=schema_c_data['duration'],
                fps=schema_c_data['fps'],
                total_frames=schema_c_data['total_frames'],
                metadata=schema_c_data.get('metadata', {}),
                created_at=schema_c_data.get('created_at')
            )
            
            # Load characters
            for char_id, char_data in schema_c_data.get('characters', {}).items():
                character = CharacterInfo(**char_data)
                schema_c.add_character(character)
            
            # Load detections
            for det_data in schema_c_data.get('detections', []):
                detection = FaceDetection(**det_data)
                schema_c.detections.append(detection)
            
            # Use advanced matcher
            matcher = AdvancedCharacterMatcher(enable_learning=True)
            schema_d = matcher.match_with_continuity(
                schema_a=schema_a,
                schema_c=schema_c,
                schema_b=schema_b
            )
            
            # Save results
            schema_d_path = fusion_output_dir / "schema_d_matches.json"
            schema_d.save_json(str(schema_d_path))
            
            # Save character profiles
            profiles_path = fusion_output_dir / "character_profiles.json"
            with open(profiles_path, 'w') as f:
                profiles_data = {}
                for char_id, profile in matcher.character_profiles.items():
                    profiles_data[char_id] = {
                        'dialogue_count': len(profile.dialogue_history),
                        'speaker_associations': profile.speaker_associations,
                        'visual_attributes': profile.visual_attributes,
                        'avg_position': profile.avg_screen_position
                    }
                json.dump(profiles_data, f, indent=2)
            
            fusion_time = time.time() - start_time
            self.performance_metrics['fusion_time'] = fusion_time
            
            # Generate comprehensive report
            self._generate_comprehensive_report(schema_d, fusion_output_dir, matcher)
            
            logger.info(f"Fusion complete in {fusion_time:.1f}s")
            logger.info(f"Matches: {len(schema_d.matches)}/{len(schema_a.segments)} "
                       f"({len(schema_d.matches)/len(schema_a.segments)*100:.1f}%)")
            
            return fusion_output_dir
            
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            raise
    
    def run_complete_robust_pipeline(self, 
                                   video_path: str, 
                                   whisper_model: str = "auto") -> dict:
        """Run the complete robust pipeline"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("ROBUST CHARACTER-DIALOGUE ANALYSIS PIPELINE")
        logger.info("="*60)
        logger.info(f"Video: {video_path}")
        logger.info(f"Session: {self.session_dir}")
        logger.info("="*60)
        
        results = {
            'video': video_path,
            'session_dir': str(self.session_dir),
            'success': False,
            'error': None,
            'performance_metrics': {}
        }
        
        try:
            # Stage 1: Audio
            audio_dir = self.run_audio_pipeline(video_path, whisper_model)
            results['audio_dir'] = str(audio_dir)
            
            # Stage 2: Visual with robust extraction
            schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
            visual_dir = self.run_robust_visual_pipeline(video_path, schema_a_path)
            results['visual_dir'] = str(visual_dir)
            
            # Stage 3: Advanced Fusion
            fusion_dir = self.run_advanced_fusion(audio_dir, visual_dir)
            results['fusion_dir'] = str(fusion_dir)
            
            # Overall metrics
            total_time = time.time() - start_time
            self.performance_metrics['total_time'] = total_time
            results['performance_metrics'] = self.performance_metrics
            results['success'] = True
            
            # Generate final report
            self._generate_final_report(results)
            
            # Calculate and log final statistics
            self._log_final_statistics(fusion_dir)
            
            logger.info("="*60)
            logger.info("ROBUST PIPELINE COMPLETE!")
            logger.info(f"Total time: {total_time:.1f}s")
            logger.info(f"Results: {self.session_dir}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results['error'] = str(e)
            results['performance_metrics'] = self.performance_metrics
            
        return results
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        return frame_count / fps if fps > 0 else 0
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def _validate_audio_output(self, audio_dir: Path):
        """Validate audio output for quality issues"""
        schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
        
        with open(schema_a_path, 'r') as f:
            schema_a = json.load(f)
        
        # Check for hallucinations (repeated text)
        texts = [seg['text'] for seg in schema_a['segments']]
        unique_texts = set(texts)
        
        if len(unique_texts) < len(texts) * 0.5:
            logger.warning(f"Potential hallucination detected: {len(unique_texts)} unique out of {len(texts)} total")
            
            # TODO: Implement fallback strategy (e.g., try different Whisper model)
    
    def _identify_temporal_gaps(self, 
                              frames: List[Dict],
                              dialogue_segments: List,
                              schema_c) -> List[Tuple[float, float]]:
        """Identify temporal gaps that need filling"""
        gaps = []
        
        # Get frame timestamps
        frame_times = sorted([f['timestamp'] for f in frames])
        
        # Find gaps larger than 30 seconds during dialogue periods
        for i in range(len(frame_times) - 1):
            gap_start = frame_times[i]
            gap_end = frame_times[i + 1]
            gap_duration = gap_end - gap_start
            
            if gap_duration > 30:  # 30 second gap
                # Check if any dialogue occurs in this gap
                dialogue_in_gap = any(
                    gap_start <= seg.start_time <= gap_end or
                    gap_start <= seg.end_time <= gap_end
                    for seg in dialogue_segments
                )
                
                if dialogue_in_gap:
                    gaps.append((gap_start + 5, gap_end - 5))  # Leave 5s buffer
        
        return gaps[:5]  # Limit to 5 gaps to avoid over-extraction
    
    def _merge_schemas(self, schema1: 'SchemaC', schema2: 'SchemaC') -> 'SchemaC':
        """Merge two Schema C objects"""
        # This is a simplified merge - could be enhanced
        for char_id, char_info in schema2.characters.items():
            if char_id not in schema1.characters:
                schema1.add_character(char_info)
        
        schema1.detections.extend(schema2.detections)
        
        return schema1
    
    def _generate_comprehensive_report(self, schema_d, output_dir: Path, matcher):
        """Generate comprehensive matching report"""
        report_path = output_dir / "robust_matching_report.md"
        
        matched = len(schema_d.matches)
        total = len(schema_d.matches) + len(schema_d.unmatched_dialogues)
        
        with open(report_path, 'w') as f:
            f.write(f"# Robust Character-Dialogue Matching Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Video ID:** {schema_d.video_id}\n")
            f.write(f"**Pipeline Version:** Robust Multi-Strategy\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- Total dialogues: {total}\n")
            f.write(f"- Matched: {matched} ({matched/total*100:.1f}%)\n")
            f.write(f"- Unmatched: {len(schema_d.unmatched_dialogues)}\n\n")
            
            if hasattr(schema_d, 'metadata') and 'confidence_calibration' in schema_d.metadata:
                f.write(f"## Confidence Calibration\n")
                calib = schema_d.metadata['confidence_calibration']
                f.write(f"- Min confidence: {calib.get('min_confidence', 'N/A')}\n")
                f.write(f"- Temporal window: {calib.get('temporal_window', 'N/A')}s\n")
                f.write(f"- Require visible: {calib.get('require_visible', 'N/A')}\n\n")
            
            # Character statistics
            f.write(f"## Character Statistics\n")
            char_dialogue_counts = {}
            char_confidence_scores = {}
            
            for match in schema_d.matches:
                char_id = match.character_id
                if char_id not in char_dialogue_counts:
                    char_dialogue_counts[char_id] = 0
                    char_confidence_scores[char_id] = []
                
                char_dialogue_counts[char_id] += 1
                if match.matching_score:
                    char_confidence_scores[char_id].append(match.matching_score.final_score)
            
            for char_id in sorted(char_dialogue_counts.keys()):
                count = char_dialogue_counts[char_id]
                avg_conf = np.mean(char_confidence_scores[char_id]) if char_confidence_scores[char_id] else 0
                
                f.write(f"\n### Character {char_id}\n")
                f.write(f"- Dialogues: {count}\n")
                f.write(f"- Average confidence: {avg_conf:.3f}\n")
                
                # Add character profile info if available
                if hasattr(matcher, 'character_profiles') and char_id in matcher.character_profiles:
                    profile = matcher.character_profiles[char_id]
                    if profile.speaker_associations:
                        best_speaker = profile.get_best_speaker()
                        if best_speaker:
                            f.write(f"- Primary speaker: {best_speaker[0]} (conf: {best_speaker[1]:.3f})\n")
            
            # Sample matches
            f.write(f"\n## Sample Matches\n")
            
            # Show high confidence matches
            high_conf_matches = [m for m in schema_d.matches if m.matching_score and m.matching_score.final_score > 0.7]
            if high_conf_matches:
                f.write(f"\n### High Confidence Matches\n")
                for match in high_conf_matches[:5]:
                    dialogue = match.dialogue_segment
                    f.write(f"\n- **Character {match.character_id}**: \"{dialogue.text[:50]}...\"\n")
                    f.write(f"  - Time: {dialogue.start_time:.1f}s - {dialogue.end_time:.1f}s\n")
                    f.write(f"  - Confidence: {match.matching_score.final_score:.3f}\n")
                    if dialogue.emotion:
                        f.write(f"  - Emotion: {dialogue.emotion}\n")
            
            # Show low confidence matches for transparency
            low_conf_matches = [m for m in schema_d.matches if m.matching_score and m.matching_score.final_score < 0.5]
            if low_conf_matches:
                f.write(f"\n### Low Confidence Matches (for review)\n")
                for match in low_conf_matches[:3]:
                    dialogue = match.dialogue_segment
                    f.write(f"\n- **Character {match.character_id}**: \"{dialogue.text[:50]}...\"\n")
                    f.write(f"  - Time: {dialogue.start_time:.1f}s - {dialogue.end_time:.1f}s\n")
                    f.write(f"  - Confidence: {match.matching_score.final_score:.3f}\n")
            
            # Unmatched analysis
            if schema_d.unmatched_dialogues:
                f.write(f"\n## Unmatched Dialogue Analysis\n")
                f.write(f"Total unmatched: {len(schema_d.unmatched_dialogues)}\n\n")
                
                # Group by time ranges
                early = [d for d in schema_d.unmatched_dialogues if d.start_time < 60]
                middle = [d for d in schema_d.unmatched_dialogues if 60 <= d.start_time < schema_d.duration - 60]
                late = [d for d in schema_d.unmatched_dialogues if d.start_time >= schema_d.duration - 60]
                
                f.write(f"- Early (first minute): {len(early)}\n")
                f.write(f"- Middle: {len(middle)}\n")
                f.write(f"- Late (last minute): {len(late)}\n")
    
    def _generate_final_report(self, results):
        """Generate final pipeline report"""
        report_path = self.session_dir / "ROBUST_PIPELINE_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Robust Pipeline Execution Report\n\n")
            f.write(f"**Session:** {self.timestamp}\n")
            f.write(f"**Video:** {results['video']}\n")
            f.write(f"**Status:** {'✅ Success' if results['success'] else '❌ Failed'}\n\n")
            
            f.write("## Performance Metrics\n")
            metrics = results.get('performance_metrics', {})
            for metric, value in metrics.items():
                if 'time' in metric:
                    f.write(f"- {metric.replace('_', ' ').title()}: {value:.1f}s\n")
                else:
                    f.write(f"- {metric.replace('_', ' ').title()}: {value}\n")
            
            f.write("\n## Output Locations\n")
            f.write(f"- Audio: `{results.get('audio_dir', 'N/A')}`\n")
            f.write(f"- Visual: `{results.get('visual_dir', 'N/A')}`\n")
            f.write(f"- Fusion: `{results.get('fusion_dir', 'N/A')}`\n")
            
            if results.get('error'):
                f.write(f"\n## ❌ Error\n```\n{results['error']}\n```\n")
            
            f.write("\n## Next Steps\n")
            f.write("1. Review the matching report in fusion_output/\n")
            f.write("2. Check character profiles for speaker associations\n")
            f.write("3. Validate low-confidence matches manually\n")
            f.write("4. Use the results for downstream applications\n")
    
    def _log_final_statistics(self, fusion_dir: Path):
        """Log final statistics"""
        # Load Schema D
        schema_d_path = fusion_dir / "schema_d_matches.json"
        with open(schema_d_path, 'r') as f:
            schema_d = json.load(f)
        
        matched = len(schema_d.get('matches', []))
        total_dialogues = matched + len(schema_d.get('unmatched_dialogues', []))
        
        if matched > 0:
            confidences = []
            for match in schema_d['matches']:
                if 'matching_score' in match and 'final_score' in match['matching_score']:
                    confidences.append(match['matching_score']['final_score'])
            
            if confidences:
                logger.info(f"\n📊 Final Statistics:")
                logger.info(f"  - Match rate: {matched}/{total_dialogues} ({matched/total_dialogues*100:.1f}%)")
                logger.info(f"  - Average confidence: {np.mean(confidences):.3f}")
                logger.info(f"  - Confidence range: {np.min(confidences):.3f} - {np.max(confidences):.3f}")
                
                high_conf = sum(1 for c in confidences if c > 0.7)
                medium_conf = sum(1 for c in confidences if 0.4 <= c <= 0.7)
                low_conf = sum(1 for c in confidences if c < 0.4)
                
                logger.info(f"  - High confidence (>0.7): {high_conf}")
                logger.info(f"  - Medium confidence (0.4-0.7): {medium_conf}")
                logger.info(f"  - Low confidence (<0.4): {low_conf}")


def main():
    parser = argparse.ArgumentParser(
        description="Run robust character-dialogue analysis pipeline"
    )
    parser.add_argument('video_path', help='Path to input video file')
    parser.add_argument('--output', default='output/robust_pipeline',
                       help='Base output directory')
    parser.add_argument('--whisper-model', default='auto',
                       choices=['auto', 'tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                       help='Whisper model size (auto = automatic selection)')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = RobustPipeline(args.output)
    
    # Run pipeline
    results = pipeline.run_complete_robust_pipeline(
        args.video_path,
        args.whisper_model
    )
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    sys.exit(main())