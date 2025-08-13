#!/usr/bin/env python3
"""
Complete End-to-End Pipeline for Character-Dialogue Analysis V2

This script runs the entire pipeline with better integration:
1. Audio Processing → Schema A (transcription) & Schema B (speakers)
2. Visual Processing → Schema C (characters) using enhanced pipeline
3. Fusion → Schema D (character-dialogue matching)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from pathlib import Path
from dotenv import load_dotenv

# Try to load .env from project root
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    # Try audio_processing_branch .env
    env_path = Path(__file__).parent.parent.parent / 'audio_processing_branch' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")

import argparse
import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompletePipelineV2:
    """Orchestrates the complete character-dialogue analysis pipeline V2"""
    
    def __init__(self, output_base_dir: str = "output/complete_pipeline_v2"):
        self.output_base_dir = Path(output_base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_base_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def run_audio_pipeline(self, video_path: str, whisper_model: str = "base") -> Path:
        """Run audio processing pipeline to generate Schema A and B"""
        logger.info("="*60)
        logger.info("STAGE 1: AUDIO PROCESSING")
        logger.info("="*60)
        
        # Run from visual branch but point to audio branch script
        audio_script = Path("../audio_processing_branch/scripts/complete_audio_pipeline.py").resolve()
        abs_video_path = Path(video_path).resolve()
        
        # Set audio output path
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
            
            # Find timestamped output
            audio_outputs = [d for d in audio_output_dir.glob("*") if d.is_dir()]
            if not audio_outputs:
                raise RuntimeError("No audio output directory found")
            
            audio_output_path = audio_outputs[0]
            logger.info(f"Audio processing complete. Output: {audio_output_path}")
            
            # Verify schemas exist
            schema_a = audio_output_path / "schemas" / "schema_a_transcription.json"
            if not schema_a.exists():
                raise RuntimeError(f"No Schema A found in {audio_output_path / 'schemas'}")
            
            schema_b = audio_output_path / "schemas" / "schema_b_speakers.json"
            if not schema_b.exists():
                logger.warning(f"Schema B (speaker diarization) not found - fusion will use audio only")
                
            return audio_output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio pipeline failed: {e.stderr}")
            raise
    
    def run_visual_pipeline(self, video_path: str, target_frames: int = 300) -> Path:
        """Run visual processing pipeline to generate Schema C"""
        logger.info("="*60)
        logger.info("STAGE 2: VISUAL PROCESSING (Enhanced with InsightFace + SORT)")
        logger.info("="*60)
        
        # Create a specific visual output directory to avoid timestamp issues
        visual_output_dir = self.session_dir / "visual_output"
        visual_output_dir.mkdir(exist_ok=True)
        
        # Import and run the pipeline directly instead of subprocess
        from tracked_visual_pipeline import TrackedVisualPipeline
        
        try:
            # Initialize pipeline
            pipeline = TrackedVisualPipeline(
                output_dir=str(visual_output_dir),
                device='cpu',
                min_appearances=3
            )
            
            # Process video
            logger.info(f"Processing video: {video_path}")
            schema_c = pipeline.process_video(
                video_path=video_path,
                target_frames=target_frames,
                extraction_mode='uniform'
            )
            
            logger.info(f"Visual processing complete. Characters found: {len(schema_c.characters)}")
            
            # Verify Schema C exists
            schema_c_path = visual_output_dir / "character_data_schemaC.json"
            if not schema_c_path.exists():
                raise RuntimeError("Schema C not generated")
                
            return visual_output_dir
            
        except Exception as e:
            logger.error(f"Visual pipeline failed: {e}")
            raise
    
    def run_fusion(self, audio_dir: Path, visual_dir: Path) -> Path:
        """Run fusion to generate Schema D"""
        logger.info("="*60)
        logger.info("STAGE 3: CHARACTER-DIALOGUE FUSION")
        logger.info("="*60)
        
        fusion_output_dir = self.session_dir / "fusion_output"
        
        # Import and run fusion directly
        sys.path.append(str(Path(__file__).parent.parent))
        from src.fusion.character_dialogue_matcher import CharacterDialogueMatcher
        from src.schemas import SchemaA, SchemaB, SchemaC, SchemaD
        from src.schemas import TranscriptionSegment, SpeakerSegment
        
        try:
            # Load schemas
            logger.info("Loading schemas...")
            
            # Load Schema A (now includes emotions)
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
            
            # Load Schema B
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
            
            # Load Schema C manually from JSON
            schema_c_path = visual_dir / "character_data_schemaC.json"
            with open(schema_c_path, 'r') as f:
                schema_c_data = json.load(f)
            
            # Create SchemaC object from data
            from src.schemas import CharacterInfo
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
            
            # Create matcher and run fusion
            from src.fusion.character_dialogue_matcher import FusionConfig
            config = FusionConfig(use_llm=False, heuristic_weight=1.0, llm_weight=0.0)
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
            
            # Generate report
            report_path = fusion_output_dir / "fusion_report.md"
            self._generate_fusion_report(schema_d, report_path)
            
            logger.info(f"Fusion complete. Matches: {len(schema_d.matches)}/{len(schema_a.segments)}")
            
            return fusion_output_dir
            
        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            raise
    
    def _generate_fusion_report(self, schema_d, report_path: Path):
        """Generate detailed fusion report"""
        matched = len(schema_d.matches)
        total = len(schema_d.matches) + len(schema_d.unmatched_dialogues)
        
        with open(report_path, 'w') as f:
            f.write(f"# Character-Dialogue Fusion Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Video ID:** {schema_d.video_id}\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- Total dialogues: {total}\n")
            f.write(f"- Matched: {matched} ({matched/total*100:.1f}%)\n")
            f.write(f"- Unmatched: {len(schema_d.unmatched_dialogues)}\n\n")
            
            f.write(f"## Matches by Character\n")
            char_counts = {}
            for match in schema_d.matches:
                char_id = match.character_id
                char_counts[char_id] = char_counts.get(char_id, 0) + 1
            
            for char_id, count in sorted(char_counts.items()):
                f.write(f"- Character {char_id}: {count} dialogues\n")
            
            f.write(f"\n## Sample Matches\n")
            for i, match in enumerate(schema_d.matches[:5]):
                dialogue = match.dialogue_segment
                f.write(f"\n### Match {i+1}\n")
                f.write(f"- Character: {match.character_id}\n")
                f.write(f"- Text: \"{dialogue.text}\"\n")
                f.write(f"- Time: {dialogue.start_time:.1f}s - {dialogue.end_time:.1f}s\n")
                if match.matching_score:
                    f.write(f"- Confidence: {match.matching_score.final_score:.2f}\n")
    
    def run_complete_pipeline(self, video_path: str, whisper_model: str = "base", 
                            target_frames: int = 300) -> dict:
        """Run the complete pipeline and return results"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("COMPLETE CHARACTER-DIALOGUE ANALYSIS PIPELINE V2")
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
            
            # Stage 2: Visual
            visual_start = time.time()
            visual_dir = self.run_visual_pipeline(video_path, target_frames)
            results['timings']['visual'] = time.time() - visual_start
            results['visual_dir'] = str(visual_dir)
            
            # Stage 3: Fusion
            fusion_start = time.time()
            fusion_dir = self.run_fusion(audio_dir, visual_dir)
            results['timings']['fusion'] = time.time() - fusion_start
            results['fusion_dir'] = str(fusion_dir)
            
            # Overall stats
            results['timings']['total'] = time.time() - start_time
            results['success'] = True
            
            # Generate final report
            self._generate_final_report(results)
            
            logger.info("="*60)
            logger.info("PIPELINE COMPLETE!")
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
        report_path = self.session_dir / "COMPLETE_PIPELINE_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Complete Pipeline Report\n\n")
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
        description="Run complete character-dialogue analysis pipeline V2"
    )
    parser.add_argument('video_path', help='Path to input video file')
    parser.add_argument('--output', default='output/complete_pipeline_v2',
                       help='Base output directory')
    parser.add_argument('--whisper-model', default='large-v3',
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                       help='Whisper model size (default: large-v3 - production model)')
    parser.add_argument('--target-frames', type=int, default=300,
                       help='Number of frames to process')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = CompletePipelineV2(args.output)
    
    # Run pipeline
    results = pipeline.run_complete_pipeline(
        args.video_path,
        args.whisper_model,
        args.target_frames
    )
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    sys.exit(main())