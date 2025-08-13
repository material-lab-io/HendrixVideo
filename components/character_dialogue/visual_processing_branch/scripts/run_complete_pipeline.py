#!/usr/bin/env python3
"""
Complete End-to-End Pipeline for Character-Dialogue Analysis

This script runs the entire pipeline:
1. Audio Processing → Schema A (transcription) & Schema B (speakers)
2. Visual Processing → Schema C (characters)
3. Fusion → Schema D (character-dialogue matching)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompletePipeline:
    """Orchestrates the complete character-dialogue analysis pipeline"""
    
    def __init__(self, output_base_dir: str = "output/complete_pipeline"):
        self.output_base_dir = Path(output_base_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_base_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def run_audio_pipeline(self, video_path: str) -> Path:
        """Run audio processing pipeline to generate Schema A and B"""
        logger.info("="*60)
        logger.info("STAGE 1: AUDIO PROCESSING")
        logger.info("="*60)
        
        # Change to audio processing directory
        audio_dir = Path("../audio_processing_branch").resolve()
        
        # Convert video path to absolute
        abs_video_path = Path(video_path).resolve()
        
        # Run complete audio pipeline
        cmd = [
            sys.executable,
            str(audio_dir / "scripts" / "complete_audio_pipeline.py"),
            str(abs_video_path),
            "--whisper-model", "base",
            "--output", str(self.session_dir.resolve() / "audio_output")
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            # Run from audio directory
            result = subprocess.run(
                cmd,
                cwd=str(audio_dir),
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find the output directory (audio pipeline creates a timestamped subdirectory)
            audio_output_base = self.session_dir / "audio_output"
            
            # Look for directories matching video_name_timestamp pattern
            audio_outputs = [d for d in audio_output_base.glob("*") if d.is_dir()]
            if not audio_outputs:
                # List what's in the directory for debugging
                logger.error(f"No audio output directory found in {audio_output_base}")
                if audio_output_base.exists():
                    logger.error(f"Contents: {list(audio_output_base.iterdir())}")
                raise RuntimeError("No audio output directory found")
            
            audio_output_dir = audio_outputs[0]  # Get the most recent
            
            logger.info(f"Audio processing complete. Output: {audio_output_dir}")
            
            # Check if schemas were generated
            schema_a_path = audio_output_dir / "schemas" / "schema_a_with_emotions.json"
            if not schema_a_path.exists():
                schema_a_path = audio_output_dir / "schemas" / "schema_a_transcription.json"
            
            if not schema_a_path.exists():
                raise RuntimeError("Schema A not generated")
                
            return audio_output_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio pipeline failed: {e.stderr}")
            raise
    
    def run_visual_pipeline(self, video_path: str) -> Path:
        """Run visual processing pipeline to generate Schema C"""
        logger.info("="*60)
        logger.info("STAGE 2: VISUAL PROCESSING")
        logger.info("="*60)
        
        # Use tracked visual pipeline with InsightFace + SORT
        visual_script = Path(__file__).parent / "tracked_visual_pipeline.py"
        abs_video_path = Path(video_path).resolve()
        
        cmd = [
            sys.executable,
            str(visual_script),
            str(abs_video_path),
            "--output", str(self.session_dir.resolve() / "visual_output"),
            "--target-frames", "300",
            "--extraction-mode", "uniform",
            "--min-appearances", "3"
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # The tracked visual pipeline creates a timestamped directory at the session level
            visual_output_base = self.session_dir
            
            # Find the actual output directory (starts with visual_output_)
            visual_outputs = [d for d in visual_output_base.glob("visual_output_*") if d.is_dir()]
            if not visual_outputs:
                logger.error(f"No visual output directory found in {visual_output_base}")
                raise RuntimeError("No visual output directory found")
            
            visual_output_dir = visual_outputs[0]
            logger.info(f"Visual processing complete. Output: {visual_output_dir}")
            
            # Check if Schema C was generated - tracked pipeline uses this name
            schema_c_path = visual_output_dir / "character_data_schemaC.json"
            
            if not schema_c_path.exists():
                # List what files were created
                logger.error(f"Schema C not found. Files in {visual_output_dir}:")
                for f in visual_output_dir.rglob("*.json"):
                    logger.error(f"  - {f.relative_to(visual_output_dir)}")
                raise RuntimeError("Schema C not generated")
                
            return visual_output_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Visual pipeline failed: {e.stderr}")
            raise
    
    def run_fusion_pipeline(self, audio_dir: Path, visual_dir: Path) -> Path:
        """Run fusion pipeline to generate Schema D"""
        logger.info("="*60)
        logger.info("STAGE 3: CHARACTER-DIALOGUE FUSION")
        logger.info("="*60)
        
        fusion_script = Path(__file__).parent / "test_complete_fusion.py"
        
        cmd = [
            sys.executable,
            str(fusion_script),
            "--audio-dir", str(audio_dir),
            "--visual-dir", str(visual_dir),
            "--output", str(self.session_dir / "fusion_output"),
            "--use-llm"  # Enable LLM analysis
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find the output directory
            fusion_output_base = self.session_dir / "fusion_output"
            fusion_outputs = list(fusion_output_base.glob("fusion_*"))
            if not fusion_outputs:
                raise RuntimeError("No fusion output directory found")
            
            fusion_output_dir = fusion_outputs[0]
            
            logger.info(f"Fusion complete. Output: {fusion_output_dir}")
            
            # Check if Schema D was generated
            schema_d_path = fusion_output_dir / "schema_d_matches.json"
            if not schema_d_path.exists():
                raise RuntimeError("Schema D not generated")
                
            return fusion_output_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Fusion pipeline failed: {e.stderr}")
            raise
    
    def generate_final_report(self, audio_dir: Path, visual_dir: Path, 
                            fusion_dir: Path, video_path: str):
        """Generate comprehensive final report"""
        logger.info("Generating final report...")
        
        report_path = self.session_dir / "COMPLETE_PIPELINE_REPORT.md"
        
        # Load schemas for statistics
        # Schema A
        schema_a_path = audio_dir / "schemas" / "schema_a_with_emotions.json"
        if not schema_a_path.exists():
            schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
        
        with open(schema_a_path, 'r') as f:
            schema_a = json.load(f)
        
        # Schema B (if exists)
        schema_b_path = audio_dir / "schemas" / "schema_b_speakers.json"
        schema_b = None
        if schema_b_path.exists():
            with open(schema_b_path, 'r') as f:
                schema_b = json.load(f)
        
        # Schema C - try both possible names
        schema_c_path = visual_dir / "schema_c_enhanced.json"
        if not schema_c_path.exists():
            schema_c_path = visual_dir / "schema_c_characters.json"
        
        with open(schema_c_path, 'r') as f:
            schema_c = json.load(f)
        
        # Schema D
        schema_d_path = fusion_dir / "schema_d_matches.json"
        with open(schema_d_path, 'r') as f:
            schema_d = json.load(f)
        
        with open(report_path, 'w') as f:
            f.write("# Complete Character-Dialogue Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Video:** {Path(video_path).name}\n")
            f.write(f"**Duration:** {schema_a['duration']:.1f}s\n\n")
            
            f.write("## Pipeline Summary\n\n")
            
            # Audio results
            f.write("### 📢 Audio Processing (Schema A & B)\n\n")
            f.write(f"- **Transcription segments:** {len(schema_a['segments'])}\n")
            f.write(f"- **Language detected:** English\n")
            
            # Get emotion distribution
            emotions = {}
            for seg in schema_a['segments']:
                if 'emotion' in seg and seg['emotion']:
                    emotions[seg['emotion']] = emotions.get(seg['emotion'], 0) + 1
            
            if emotions:
                f.write(f"- **Emotions detected:** {', '.join(f'{e} ({c})' for e, c in emotions.items())}\n")
            
            if schema_b:
                f.write(f"- **Speakers identified:** {schema_b['num_speakers']}\n")
            else:
                f.write("- **Speaker diarization:** Not available (HF_TOKEN required)\n")
            
            f.write("\n")
            
            # Visual results
            f.write("### 👁️ Visual Processing (Schema C)\n\n")
            f.write(f"- **Unique characters found:** {len(schema_c['characters'])}\n")
            f.write(f"- **Face detections:** {len(schema_c['detections'])}\n")
            
            # Character details
            for char_id, char in schema_c['characters'].items():
                f.write(f"\n**Character {char_id}:**\n")
                f.write(f"- Appearances: {char['num_appearances']}\n")
                f.write(f"- Screen time: {char['total_screen_time']:.1f}s\n")
                if char.get('attributes'):
                    attrs = char['attributes']
                    f.write(f"- Demographics: {attrs.get('dominant_gender', 'N/A')}, ")
                    if 'age' in attrs and isinstance(attrs['age'], dict):
                        f.write(f"Age ~{attrs['age'].get('median', 'N/A')}\n")
                    else:
                        f.write("Age N/A\n")
            
            f.write("\n")
            
            # Fusion results
            f.write("### 🔀 Character-Dialogue Fusion (Schema D)\n\n")
            summary = schema_d['matching_summary']
            f.write(f"- **Dialogues matched:** {summary['matched_dialogues']}/{summary['total_dialogues']} ")
            f.write(f"({summary['matching_rate']*100:.1f}%)\n")
            f.write(f"- **Average confidence:** {summary['average_confidence']:.2f}\n")
            
            # Confidence distribution
            conf = summary['confidence_distribution']
            f.write(f"- **Confidence breakdown:**\n")
            f.write(f"  - High: {conf['high']}\n")
            f.write(f"  - Medium: {conf['medium']}\n")
            f.write(f"  - Low: {conf['low']}\n")
            
            # Character dialogue assignments
            f.write(f"\n**Character Dialogue Assignments:**\n")
            for char_id, count in summary['character_dialogue_counts'].items():
                f.write(f"- Character {char_id}: {count} dialogues\n")
            
            f.write("\n## Sample Results\n\n")
            
            # Show first few matches
            matches = schema_d['matches'][:5]
            for i, match in enumerate(matches, 1):
                dialogue = match['dialogue']
                score = match['matching_score']
                
                f.write(f"### Match {i}\n")
                f.write(f"**Time:** [{dialogue['start_time']:.1f}s - {dialogue['end_time']:.1f}s]\n")
                f.write(f"**Character:** {match['character_id']}\n")
                f.write(f"**Dialogue:** \"{dialogue['text'][:100]}...\"\n")
                f.write(f"**Confidence:** {score['confidence_level']} ({score['final_score']:.2f})\n")
                f.write(f"**Reasoning:** {score['reasoning']}\n\n")
            
            f.write("## Output Files\n\n")
            f.write(f"- **Schema A (Transcription):** `{schema_a_path.relative_to(self.session_dir)}`\n")
            if schema_b:
                f.write(f"- **Schema B (Speakers):** `{schema_b_path.relative_to(self.session_dir)}`\n")
            f.write(f"- **Schema C (Characters):** `{schema_c_path.relative_to(self.session_dir)}`\n")
            f.write(f"- **Schema D (Matches):** `{schema_d_path.relative_to(self.session_dir)}`\n")
            
            f.write(f"\n## Session Directory\n\n")
            f.write(f"All outputs saved to: `{self.session_dir}`\n")
        
        logger.info(f"Final report saved to: {report_path}")
        return report_path
    
    def run_complete_pipeline(self, video_path: str):
        """Run the complete end-to-end pipeline"""
        start_time = time.time()
        
        logger.info("="*60)
        logger.info("COMPLETE CHARACTER-DIALOGUE ANALYSIS PIPELINE")
        logger.info("="*60)
        logger.info(f"Video: {video_path}")
        logger.info(f"Session: {self.session_dir}")
        logger.info("="*60)
        
        try:
            # Stage 1: Audio Processing
            audio_output_dir = self.run_audio_pipeline(video_path)
            
            # Stage 2: Visual Processing
            visual_output_dir = self.run_visual_pipeline(video_path)
            
            # Stage 3: Fusion
            fusion_output_dir = self.run_fusion_pipeline(
                audio_output_dir, visual_output_dir
            )
            
            # Generate final report
            report_path = self.generate_final_report(
                audio_output_dir, visual_output_dir, 
                fusion_output_dir, video_path
            )
            
            # Calculate total time
            total_time = time.time() - start_time
            
            print("\n" + "="*60)
            print("🎉 COMPLETE PIPELINE SUCCESS! 🎉")
            print("="*60)
            print(f"Total processing time: {total_time:.1f}s")
            print(f"\nAll outputs saved to: {self.session_dir}")
            print(f"\nFinal report: {report_path}")
            print("\nGenerated schemas:")
            print("  ✅ Schema A - Dialogue transcriptions with emotions")
            print("  ✅ Schema B - Speaker diarization (if HF_TOKEN set)")
            print("  ✅ Schema C - Character detection and tracking")
            print("  ✅ Schema D - Character-dialogue matches")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(
        description="Run complete character-dialogue analysis pipeline"
    )
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("--output", default="output/complete_pipeline",
                       help="Base output directory")
    parser.add_argument("--whisper-model", default="base",
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                       help="Whisper model size")
    
    args = parser.parse_args()
    
    # Check video exists
    if not Path(args.video_path).exists():
        logger.error(f"Video not found: {args.video_path}")
        return
    
    # Set environment variable for TensorFlow
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    
    # Create and run pipeline
    pipeline = CompletePipeline(args.output)
    
    try:
        pipeline.run_complete_pipeline(args.video_path)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()