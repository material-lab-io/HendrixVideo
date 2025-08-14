#!/usr/bin/env python3
"""
Complete Audio Processing Pipeline with GPU Optimization
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
import torch

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
    """Run complete audio processing pipeline with GPU optimization
    
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
    
    # Check GPU availability
    gpu_available = torch.cuda.is_available()
    device = "cuda" if gpu_available else "cpu"
    
    print("\n" + "="*60)
    print("COMPLETE AUDIO PROCESSING PIPELINE (GPU OPTIMIZED)")
    print("="*60)
    print(f"Video: {video_path.name}")
    print(f"Output: {output_paths['root']}")
    print(f"Device: {device.upper()} {'✓' if gpu_available else '(GPU not available)'}")
    if gpu_available:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print("-"*60)
    
    # Pipeline timing
    pipeline_start = time.time()
    results = {
        'video': str(video_path),
        'start_time': datetime.now().isoformat(),
        'device': device,
        'gpu_available': gpu_available,
        'outputs': {},
        'timings': {},
        'errors': []
    }
    
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
    
    # Step 1: Whisper ASR with GPU
    print("\n[1/3] Running Whisper ASR...")
    try:
        start_time = time.time()
        
        # Configure Whisper with explicit GPU device
        whisper_config = WhisperConfig(
            model_name=whisper_model,
            device=device,  # Explicitly set device
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
        print(f"  Processing speed: {duration/whisper_time:.1f}x realtime")
        
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
            
            # Calculate emotion coverage
            segments_with_emotion = sum(1 for s in schema_a.segments if s.emotion)
            emotion_coverage = (segments_with_emotion / len(schema_a.segments) * 100) if schema_a.segments else 0
            
            print(f"✓ Emotion analysis complete: {emotion_coverage:.1f}% coverage in {emotion_time:.1f}s")
            
        except Exception as e:
            logger.error(f"Emotion recognition failed: {e}")
            results['errors'].append(f"Emotion: {str(e)}")
            print(f"✗ Emotion analysis failed: {e}")
    
    # Step 3: Speaker Diarization
    print("\n[3/3] Running Speaker Diarization...")
    try:
        start_time = time.time()
        
        # Use flexible diarization processor
        diarization_processor = FlexibleDiarizationProcessor()
        
        # Configure diarization with provided speaker hints
        kwargs = {}
        if num_speakers is not None:
            kwargs['num_speakers'] = num_speakers
        if min_speakers is not None:
            kwargs['min_speakers'] = min_speakers
        if max_speakers is not None:
            kwargs['max_speakers'] = max_speakers
        
        schema_b = diarization_processor.process_audio(str(audio_path), **kwargs)
        
        # Save Schema B
        schema_b_path = output_paths['schemas'] / 'schema_b_speakers.json'
        schema_b.save_json(str(schema_b_path))
        
        diarization_time = time.time() - start_time
        results['timings']['diarization'] = diarization_time
        results['outputs']['schema_b_speakers'] = str(schema_b_path)
        
        # Get unique speakers
        unique_speakers = len(set(s.speaker_id for s in schema_b.segments))
        
        print(f"✓ Diarization complete: {unique_speakers} speakers, {len(schema_b.segments)} segments in {diarization_time:.1f}s")
        
    except Exception as e:
        logger.error(f"Speaker diarization failed: {e}")
        results['errors'].append(f"Diarization: {str(e)}")
        print(f"✗ Diarization failed: {e}")
        schema_b = None
    
    # Summary
    pipeline_time = time.time() - pipeline_start
    results['timings']['total'] = pipeline_time
    
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Total time: {pipeline_time:.1f}s ({pipeline_time/60:.1f} minutes)")
    print(f"Processing speed: {duration/pipeline_time:.1f}x realtime")
    
    if results['errors']:
        print(f"\nErrors encountered: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    print(f"\nOutputs saved to: {output_paths['root']}")
    
    # Save pipeline results
    results_path = output_paths['reports'] / 'pipeline_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return output_paths['root']


def main():
    parser = argparse.ArgumentParser(
        description="Complete audio processing pipeline with Schema A and B generation (GPU optimized)"
    )
    parser.add_argument(
        "video",
        help="Path to input video file"
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: base)"
    )
    parser.add_argument(
        "--emotion-model",
        default="superb/wav2vec2-large-superb-er",
        help="Emotion recognition model"
    )
    parser.add_argument(
        "--num-speakers",
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
        "--output",
        default="output/pipeline",
        help="Base output directory"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    # Run pipeline
    try:
        output_dir = process_complete_pipeline(
            args.video,
            args.output,
            args.whisper_model,
            args.emotion_model,
            args.num_speakers,
            args.min_speakers,
            args.max_speakers,
            args.verbose
        )
        print(f"\nPipeline completed successfully!")
        print(f"Results in: {output_dir}")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()