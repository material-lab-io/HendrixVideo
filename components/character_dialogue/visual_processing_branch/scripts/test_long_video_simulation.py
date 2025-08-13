#!/usr/bin/env python3
"""
Simulate testing on a long video by showing what the pipeline would produce
for a hypothetical 30-minute video with multiple characters and dialogues.
"""

import json
from datetime import datetime
from pathlib import Path
import random
import numpy as np

def create_simulated_long_video_schemas():
    """Create realistic schema outputs for a 30-minute video"""
    
    video_id = "long_documentary_sample"
    duration = 1800.0  # 30 minutes
    fps = 24.0
    total_frames = int(duration * fps)
    
    # Create output directory
    output_dir = Path("output/simulated_long_video")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("SIMULATED LONG VIDEO ANALYSIS")
    print("Video: Documentary Sample (30 minutes)")
    print("="*80)
    
    # Schema A - Transcription (150 dialogues for 30 min)
    print("\n[1] SCHEMA A - TRANSCRIPTION DATA")
    print("-"*40)
    
    segments = []
    emotions = ["neutral", "happy", "sad", "angry", "surprise", "fear"]
    current_time = 30.0  # Start after intro
    
    for i in range(150):
        duration = random.uniform(2.0, 8.0)
        gap = random.uniform(3.0, 15.0)
        
        segment = {
            "segment_id": f"SEG_{i:04d}",
            "start_time": round(current_time, 1),
            "end_time": round(current_time + duration, 1),
            "text": f"Sample dialogue {i+1} discussing the topic in detail...",
            "confidence": round(random.uniform(0.7, 0.95), 3),
            "emotion": random.choice(emotions),
            "emotion_confidence": round(random.uniform(0.5, 0.9), 3),
            "language": "en",
            "source": "whisper"
        }
        segments.append(segment)
        current_time += duration + gap
        
        if i < 5:  # Show first 5
            print(f"\n  Segment {i+1}: {segment['start_time']:.1f}s - {segment['end_time']:.1f}s")
            print(f"  Text: \"{segment['text'][:50]}...\"")
            print(f"  Emotion: {segment['emotion']} ({segment['emotion_confidence']:.2f})")
    
    schema_a = {
        "video_id": video_id,
        "duration": duration,
        "segments": segments,
        "metadata": {
            "whisper_model": "base",
            "language": "en",
            "total_segments": len(segments)
        },
        "created_at": datetime.now().isoformat()
    }
    
    print(f"\n  Total Segments: {len(segments)}")
    print(f"  Duration Coverage: {sum(s['end_time']-s['start_time'] for s in segments):.1f}s")
    print(f"  Average Confidence: {np.mean([s['confidence'] for s in segments]):.3f}")
    
    # Schema B - Speaker Diarization
    print("\n\n[2] SCHEMA B - SPEAKER DIARIZATION")
    print("-"*40)
    
    num_speakers = 8  # Documentary with multiple speakers
    speaker_segments = []
    speaker_times = {f"SPEAKER_{i:02d}": 0 for i in range(num_speakers)}
    
    # Assign speakers to dialogue segments
    for seg in segments:
        # Main speakers more likely
        if random.random() < 0.6:
            speaker_id = f"SPEAKER_{random.choice([0, 1, 2]):02d}"
        else:
            speaker_id = f"SPEAKER_{random.randint(3, num_speakers-1):02d}"
        
        speaker_seg = {
            "segment_id": f"SPKR_{len(speaker_segments):04d}",
            "speaker_id": speaker_id,
            "start_time": seg["start_time"],
            "end_time": seg["end_time"],
            "confidence": round(random.uniform(0.8, 0.95), 3)
        }
        speaker_segments.append(speaker_seg)
        speaker_times[speaker_id] += seg["end_time"] - seg["start_time"]
    
    schema_b = {
        "video_id": video_id,
        "duration": duration,
        "num_speakers": num_speakers,
        "segments": speaker_segments,
        "metadata": {},
        "created_at": datetime.now().isoformat()
    }
    
    print(f"  Number of Speakers: {num_speakers}")
    print(f"  Speaker Distribution:")
    for speaker, time in sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    - {speaker}: {time:.1f}s ({time/duration*100:.1f}%)")
    
    # Schema C - Visual/Character Data
    print("\n\n[3] SCHEMA C - VISUAL/CHARACTER DATA")
    print("-"*40)
    
    num_characters = 12  # Multiple interviewees
    characters = {}
    detections = []
    
    for i in range(num_characters):
        char_id = str(i+1)
        appearances = random.randint(10, 100)
        first_appear = random.uniform(0, duration/3)
        last_appear = random.uniform(2*duration/3, duration)
        
        characters[char_id] = {
            "character_id": char_id,
            "num_appearances": appearances,
            "first_appearance": round(first_appear, 1),
            "last_appearance": round(last_appear, 1),
            "total_screen_time": round(random.uniform(30, 300), 1),
            "average_confidence": round(random.uniform(0.85, 0.95), 3),
            "representative_embeddings": [[random.random() for _ in range(512)] for _ in range(10)],
            "appearance_segments": [
                {"start": round(first_appear + j*10, 1), 
                 "end": round(first_appear + j*10 + 5, 1)} 
                for j in range(5)
            ]
        }
        
        # Create some detections
        for j in range(min(20, appearances)):
            det_time = random.uniform(first_appear, last_appear)
            detection = {
                "detection_id": f"DET_{len(detections):05d}",
                "frame_number": int(det_time * fps),
                "timestamp": round(det_time, 1),
                "character_id": char_id,
                "bbox": [0.3, 0.2, 0.7, 0.8],
                "confidence": round(random.uniform(0.85, 0.95), 3)
            }
            detections.append(detection)
    
    schema_c = {
        "video_id": video_id,
        "duration": duration,
        "fps": fps,
        "total_frames": total_frames,
        "characters": characters,
        "detections": sorted(detections, key=lambda x: x['timestamp']),
        "metadata": {
            "processing_mode": "adaptive_extraction",
            "frames_processed": 1500
        },
        "created_at": datetime.now().isoformat()
    }
    
    print(f"  Total Characters: {num_characters}")
    print(f"  Total Detections: {len(detections)}")
    print(f"  Main Characters:")
    for i, (char_id, char) in enumerate(sorted(characters.items(), 
                                               key=lambda x: x[1]['num_appearances'], 
                                               reverse=True)[:5]):
        print(f"    - Character {char_id}: {char['num_appearances']} appearances, "
              f"{char['total_screen_time']:.1f}s screen time")
    
    # Schema D - Character-Dialogue Matches
    print("\n\n[4] SCHEMA D - CHARACTER-DIALOGUE MATCHES")
    print("-"*40)
    
    matches = []
    unmatched = []
    char_dialogue_count = {str(i+1): 0 for i in range(num_characters)}
    
    for seg in segments:
        if random.random() < 0.75:  # 75% match rate for long video
            # Assign to character based on speaker patterns
            char_id = str(random.randint(1, num_characters))
            char_dialogue_count[char_id] += 1
            
            match = {
                "match_id": f"MATCH_{len(matches):04d}",
                "character_id": char_id,
                "dialogue": seg,
                "time_overlap": round(random.uniform(0.6, 1.0), 3),
                "matching_score": {
                    "heuristic_scores": {
                        "temporal": round(random.uniform(0.3, 0.9), 3),
                        "speaker": round(random.uniform(0.4, 0.9), 3),
                        "continuity": round(random.uniform(0.5, 0.9), 3),
                        "position": round(random.uniform(0.2, 0.7), 3)
                    },
                    "llm_score": 0.0,
                    "final_score": round(random.uniform(0.5, 0.85), 3),
                    "confidence_level": "high" if random.random() > 0.3 else "medium"
                }
            }
            matches.append(match)
        else:
            unmatched.append(seg)
    
    schema_d = {
        "video_id": video_id,
        "duration": duration,
        "matches": matches,
        "unmatched_dialogues": unmatched,
        "matching_summary": {
            "total_dialogues": len(segments),
            "matched": len(matches),
            "unmatched": len(unmatched),
            "match_rate": len(matches) / len(segments)
        },
        "metadata": {
            "matching_method": "advanced_continuity",
            "confidence_calibration": {
                "min_confidence": 0.3,
                "temporal_window": 30.0,
                "require_visible": False
            }
        },
        "created_at": datetime.now().isoformat()
    }
    
    print(f"  Total Matches: {len(matches)}/{len(segments)} ({len(matches)/len(segments)*100:.1f}%)")
    print(f"  Character Dialogue Distribution:")
    for char_id, count in sorted(char_dialogue_count.items(), 
                                key=lambda x: x[1], 
                                reverse=True)[:5]:
        if count > 0:
            print(f"    - Character {char_id}: {count} dialogues")
    
    confidence_scores = [m['matching_score']['final_score'] for m in matches]
    print(f"\n  Confidence Statistics:")
    print(f"    - Average: {np.mean(confidence_scores):.3f}")
    print(f"    - Min: {np.min(confidence_scores):.3f}")
    print(f"    - Max: {np.max(confidence_scores):.3f}")
    
    # Performance simulation
    print("\n\n[5] PERFORMANCE METRICS")
    print("-"*40)
    print(f"  Simulated Processing Times (for 30-minute video):")
    print(f"    - Audio Processing: ~120s")
    print(f"    - Visual Processing: ~450s")
    print(f"    - Fusion: ~1s")
    print(f"    - Total: ~571s (9.5 minutes)")
    print(f"\n  Frame Extraction:")
    print(f"    - Target Frames: 1500")
    print(f"    - Actual Extracted: 1500")
    print(f"    - Temporal Coverage: 75%")
    print(f"    - Strategy Used: force_extract")
    
    # Save schemas
    print(f"\n\nSaving simulated schemas to: {output_dir}")
    
    # Create subdirectories
    (output_dir / "audio_output" / "video_20250803_120000" / "schemas").mkdir(parents=True, exist_ok=True)
    (output_dir / "visual_output").mkdir(parents=True, exist_ok=True)
    (output_dir / "fusion_output").mkdir(parents=True, exist_ok=True)
    
    # Save files
    with open(output_dir / "audio_output" / "video_20250803_120000" / "schemas" / "schema_a_transcription.json", 'w') as f:
        json.dump(schema_a, f, indent=2)
    
    with open(output_dir / "audio_output" / "video_20250803_120000" / "schemas" / "schema_b_speakers.json", 'w') as f:
        json.dump(schema_b, f, indent=2)
    
    with open(output_dir / "visual_output" / "character_data_schemaC.json", 'w') as f:
        json.dump(schema_c, f, indent=2)
    
    with open(output_dir / "fusion_output" / "schema_d_matches.json", 'w') as f:
        json.dump(schema_d, f, indent=2)
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    
    return output_dir


if __name__ == "__main__":
    output_dir = create_simulated_long_video_schemas()
    
    print(f"\nTo view the detailed schemas, run:")
    print(f"python scripts/display_all_schemas.py {output_dir}")
    print(f"\nTo validate the schemas, run:")
    print(f"python scripts/validate_all_schemas.py {output_dir}")