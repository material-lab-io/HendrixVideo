#!/usr/bin/env python3
"""
Complete Audio Processing Pipeline
Combines Whisper ASR, Emotion Recognition, and Speaker Diarization
Generates Schema A (with emotions) and Schema B outputs
"""

import argparse
import logging
from pathlib import Path
import time
import sys
import os
from datetime import datetime
import json
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.audio.whisper_processor import WhisperProcessor, WhisperConfig
from src.audio.emotion_processor import EmotionProcessor, EmotionConfig
from src.audio.diarization_processor import DiarizationProcessor, DiarizationConfig
from src.audio.flexible_diarization_processor import FlexibleDiarizationProcessor
from src.schemas import SchemaA, SchemaB


def setup_logging(verbose=False, log_file=None):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def create_output_structure(base_dir: str, video_name: str) -> dict:
    """Create organized output directory structure
    
    Returns dict with paths for different outputs
    """
    base_path = Path(base_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create main output directory
    output_dir = base_path / f"{video_name}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    paths = {
        'root': output_dir,
        'schemas': output_dir / 'schemas',
        'reports': output_dir / 'reports',
        'audio': output_dir / 'audio',
        'logs': output_dir / 'logs'
    }
    
    for path in paths.values():
        path.mkdir(exist_ok=True)
    
    return paths


def process_complete_pipeline(
    video_path: str,
    output_base: str = "output/pipeline",
    whisper_model: str = "base",
    emotion_model: str = "superb/wav2vec2-large-superb-er",
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    verbose: bool = False
):
    """Run complete audio processing pipeline
    
    Args:
        video_path: Path to input video
        output_base: Base directory for organized outputs
        whisper_model: Whisper model to use
        emotion_model: Emotion recognition model
        num_speakers: Known number of speakers
        min_speakers: Minimum expected speakers
        max_speakers: Maximum expected speakers
        verbose: Enable verbose logging
    """
    logger = logging.getLogger(__name__)
    
    # Setup paths
    video_path = Path(video_path)
    video_name = video_path.stem
    
    # Create output structure
    logger.info(f"Creating output structure for: {video_name}")
    output_paths = create_output_structure(output_base, video_name)
    
    # Setup logging to file
    log_file = output_paths['logs'] / 'pipeline.log'
    setup_logging(verbose, log_file)
    
    # Pipeline timing
    pipeline_start = time.time()
    results = {
        'video': str(video_path),
        'start_time': datetime.now().isoformat(),
        'outputs': {},
        'timings': {},
        'errors': []
    }
    
    print("\n" + "="*60)
    print("COMPLETE AUDIO PROCESSING PIPELINE")
    print("="*60)
    print(f"Video: {video_path.name}")
    print(f"Output: {output_paths['root']}")
    print("-"*60)
    
    # Extract audio once for all processors
    audio_path = output_paths['audio'] / f"{video_name}.wav"
    if not audio_path.exists():
        logger.info("Extracting audio from video...")
        import subprocess
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            "-y", str(audio_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Audio extracted to: {audio_path}")
    
    # Get video duration
    import subprocess
    import json as json_lib
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json_lib.loads(result.stdout)
    duration = float(info["format"]["duration"])
    
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    
    # Step 1: Whisper ASR
    print("\n[1/3] Running Whisper ASR...")
    try:
        start_time = time.time()
        
        whisper_config = WhisperConfig(
            model_name=whisper_model,
            temperature=0.0,
            word_timestamps=True
        )
        
        whisper_processor = WhisperProcessor(whisper_config)
        schema_a = whisper_processor.process_video(str(video_path))
        
        # Save initial Schema A
        schema_a_path = output_paths['schemas'] / 'schema_a_transcription.json'
        schema_a.save_json(str(schema_a_path))
        
        whisper_time = time.time() - start_time
        results['timings']['whisper'] = whisper_time
        results['outputs']['schema_a_transcription'] = str(schema_a_path)
        
        print(f"✓ Transcription complete: {len(schema_a.segments)} segments in {whisper_time:.1f}s")
        
    except Exception as e:
        logger.error(f"Whisper ASR failed: {e}")
        results['errors'].append(f"Whisper: {str(e)}")
        print(f"✗ Transcription failed: {e}")
        schema_a = None
    
    # Step 2: Emotion Recognition
    if schema_a:
        print("\n[2/3] Running Emotion Recognition...")
        try:
            start_time = time.time()
            
            emotion_config = EmotionConfig(
                model_name=emotion_model,
                batch_size=8,
                aggregation_strategy="mean"
            )
            
            emotion_processor = EmotionProcessor(emotion_config)
            # Enhance the existing schema_a in place
            schema_a = emotion_processor.enhance_schema_a(schema_a, str(audio_path))
            
            # Update the original Schema A file with emotions
            schema_a_path = output_paths['schemas'] / 'schema_a_transcription.json'
            schema_a.save_json(str(schema_a_path))
            
            emotion_time = time.time() - start_time
            results['timings']['emotion'] = emotion_time
            
            # Get emotion summary
            emotion_counts = {}
            for seg in schema_a.segments:
                if seg.emotion and seg.source == "whisper":
                    emotion_counts[seg.emotion] = emotion_counts.get(seg.emotion, 0) + 1
            
            print(f"✓ Emotion analysis complete in {emotion_time:.1f}s")
            if emotion_counts:
                print(f"  Emotions detected: {', '.join(emotion_counts.keys())}")
            else:
                print("  No emotions detected")
            
        except Exception as e:
            logger.error(f"Emotion recognition failed: {e}")
            results['errors'].append(f"Emotion: {str(e)}")
            print(f"✗ Emotion analysis failed: {e}")
    
    # Step 3: Speaker Diarization (Flexible - works with or without HF_TOKEN)
    print("\n[3/3] Running Speaker Diarization...")
    
    try:
        start_time = time.time()
        
        # Use flexible diarization processor
        diarization_processor = FlexibleDiarizationProcessor()
        
        if diarization_processor.is_available():
            print(f"  Using backend: {diarization_processor.get_backend()}")
            
            schema_b = diarization_processor.process_video(str(video_path), 
                                                          video_id=video_name,
                                                          num_speakers=num_speakers)
            
            # Merge overlapping segments if supported
            schema_b = diarization_processor.merge_overlapping_segments(schema_b, overlap_threshold=0.5)
            
            # Check if diarization was successful
            if schema_b.num_speakers > 0:
                print(f"✓ Speaker diarization complete: {schema_b.num_speakers} speakers")
            else:
                print("⚠ Speaker diarization completed but no speakers detected")
                
        else:
            print("⚠ No diarization backend available")
            print("  Options:")
            print("  1. Set HF_TOKEN for Pyannote (best quality)")
            print("  2. Install simple-diarizer: pip install simple-diarizer")
            
            # Create empty Schema B
            schema_b = SchemaB(
                video_id=video_name,
                duration=duration,
                num_speakers=0,
                metadata={
                    'status': 'no_backend',
                    'message': 'No diarization backend available'
                }
            )
            results['errors'].append("Diarization: No backend available")
        
        # Save Schema B
        schema_b_path = output_paths['schemas'] / 'schema_b_speakers.json'
        schema_b.save_json(str(schema_b_path))
        results['outputs']['schema_b'] = str(schema_b_path)
        
        diarization_time = time.time() - start_time
        results['timings']['diarization'] = diarization_time
        
    except Exception as e:
        logger.error(f"Speaker diarization failed: {e}")
        results['errors'].append(f"Diarization: {str(e)}")
        print(f"✗ Speaker diarization failed: {e}")
        
        # Create empty Schema B on error
        schema_b = SchemaB(
            video_id=video_name,
            duration=duration,
            num_speakers=0,
            metadata={
                'status': 'error',
                'error': str(e)
            }
        )
        
        # Save empty Schema B
        schema_b_path = output_paths['schemas'] / 'schema_b_speakers.json'
        schema_b.save_json(str(schema_b_path))
        results['outputs']['schema_b'] = str(schema_b_path)
    
    # Generate summary report
    print("\n" + "-"*60)
    print("Generating summary report...")
    
    report_path = output_paths['reports'] / 'pipeline_summary.json'
    results['end_time'] = datetime.now().isoformat()
    results['total_time'] = time.time() - pipeline_start
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate human-readable report
    generate_summary_report(
        output_paths,
        schema_a_emotions if 'schema_a_emotions' in locals() else schema_a,
        schema_b if 'schema_b' in locals() else None,
        results
    )
    
    # Print final summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"Total processing time: {results['total_time']:.1f}s")
    print(f"\nOutput location: {output_paths['root']}")
    print("\nGenerated files:")
    for category, path in results['outputs'].items():
        print(f"  - {category}: {Path(path).name}")
    
    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nReports:")
    print(f"  - pipeline_summary.json")
    print(f"  - audio_analysis_report.md")
    print("="*60)


def generate_summary_report(output_paths, schema_a, schema_b, results):
    """Generate human-readable summary report"""
    report_path = output_paths['reports'] / 'audio_analysis_report.md'
    
    with open(report_path, 'w') as f:
        f.write("# Audio Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overview
        f.write("## Overview\n")
        f.write(f"- **Video**: {Path(results['video']).name}\n")
        f.write(f"- **Total processing time**: {results['total_time']:.1f}s\n")
        f.write(f"- **Output location**: {output_paths['root']}\n\n")
        
        # Transcription Summary
        if schema_a:
            f.write("## Transcription (Schema A)\n")
            f.write(f"- **Segments**: {len(schema_a.segments)}\n")
            f.write(f"- **Duration**: {schema_a.duration:.1f}s\n")
            f.write(f"- **Processing time**: {results['timings'].get('whisper', 0):.1f}s\n")
            
            # Sample transcripts
            f.write("\n### Sample Transcripts\n")
            for i, seg in enumerate(schema_a.segments[:5]):
                if seg.source == "whisper":
                    f.write(f"{i+1}. [{seg.start_time:.1f}s] {seg.text}\n")
            f.write("\n")
        
        # Emotion Summary
        if schema_a and hasattr(schema_a.segments[0], 'emotion') and schema_a.segments[0].emotion:
            f.write("## Emotion Analysis\n")
            f.write(f"- **Processing time**: {results['timings'].get('emotion', 0):.1f}s\n")
            
            emotion_counts = {}
            for seg in schema_a.segments:
                if seg.emotion and seg.source == "whisper":
                    emotion_counts[seg.emotion] = emotion_counts.get(seg.emotion, 0) + 1
            
            f.write("\n### Emotion Distribution\n")
            total_emotions = sum(emotion_counts.values())
            for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_emotions * 100) if total_emotions > 0 else 0
                f.write(f"- {emotion}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
        
        # Speaker Summary
        if schema_b:
            f.write("## Speaker Diarization (Schema B)\n")
            f.write(f"- **Speakers detected**: {schema_b.num_speakers}\n")
            f.write(f"- **Segments**: {len(schema_b.segments)}\n")
            f.write(f"- **Processing time**: {results['timings'].get('diarization', 0):.1f}s\n")
            
            stats = schema_b.get_speaker_stats()
            f.write("\n### Speaker Statistics\n")
            for speaker_id, speaker_stats in sorted(stats.items()):
                f.write(f"- **{speaker_id}**: {speaker_stats['total_time']:.1f}s ({speaker_stats['percentage']:.1f}%)\n")
            f.write("\n")
        
        # Errors
        if results['errors']:
            f.write("## Errors\n")
            for error in results['errors']:
                f.write(f"- {error}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Complete Audio Processing Pipeline - Transcription, Emotions, and Speakers"
    )
    parser.add_argument(
        "video_path",
        help="Path to input video file"
    )
    parser.add_argument(
        "-o", "--output-base",
        default="output/pipeline",
        help="Base directory for organized outputs (default: output/pipeline)"
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        help="Whisper model to use (default: base)"
    )
    parser.add_argument(
        "--emotion-model",
        default="superb/wav2vec2-large-superb-er",
        help="Emotion recognition model"
    )
    parser.add_argument(
        "-n", "--num-speakers",
        type=int,
        help="Known number of speakers"
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        help="Minimum number of speakers"
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        help="Maximum number of speakers"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Check video exists
    if not Path(args.video_path).exists():
        print(f"Error: Video file not found: {args.video_path}")
        sys.exit(1)
    
    # Check HF_TOKEN for diarization
    if not os.environ.get("HF_TOKEN"):
        print("Warning: HF_TOKEN not set. Speaker diarization will be skipped.")
        print("To enable diarization: export HF_TOKEN=your_token")
    
    try:
        process_complete_pipeline(
            args.video_path,
            args.output_base,
            args.whisper_model,
            args.emotion_model,
            args.num_speakers,
            args.min_speakers,
            args.max_speakers,
            args.verbose
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()