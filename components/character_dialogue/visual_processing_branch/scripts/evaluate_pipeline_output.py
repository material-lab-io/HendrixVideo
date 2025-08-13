#!/usr/bin/env python3
"""
Pipeline Output Evaluation Script
Analyzes the quality and correctness of each schema from the complete pipeline
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import statistics
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def evaluate_schema_a(schema_path: Path) -> dict:
    """Evaluate Schema A (Transcription) quality"""
    evaluation = {
        "exists": schema_path.exists(),
        "quality_metrics": {},
        "issues": [],
        "recommendations": []
    }
    
    if not schema_path.exists():
        evaluation["issues"].append("Schema A file not found")
        return evaluation
    
    with open(schema_path, 'r') as f:
        schema_a = json.load(f)
    
    segments = schema_a.get('segments', [])
    
    # Basic metrics
    evaluation["quality_metrics"]["total_segments"] = len(segments)
    evaluation["quality_metrics"]["duration"] = schema_a.get('duration', 0)
    
    if segments:
        # Timing analysis
        start_times = [s['start_time'] for s in segments]
        end_times = [s['end_time'] for s in segments]
        segment_lengths = [s['end_time'] - s['start_time'] for s in segments]
        
        evaluation["quality_metrics"]["first_speech_time"] = min(start_times)
        evaluation["quality_metrics"]["last_speech_time"] = max(end_times)
        evaluation["quality_metrics"]["avg_segment_length"] = statistics.mean(segment_lengths)
        evaluation["quality_metrics"]["total_speech_time"] = sum(segment_lengths)
        
        # Confidence analysis
        confidences = [s.get('confidence', 0) for s in segments]
        evaluation["quality_metrics"]["avg_confidence"] = statistics.mean(confidences)
        evaluation["quality_metrics"]["min_confidence"] = min(confidences)
        
        # Check for emotions
        emotion_count = sum(1 for s in segments if s.get('emotion'))
        evaluation["quality_metrics"]["segments_with_emotions"] = emotion_count
        evaluation["quality_metrics"]["emotion_coverage"] = emotion_count / len(segments)
        
        # Issues
        if evaluation["quality_metrics"]["min_confidence"] < 0.5:
            evaluation["issues"].append("Some segments have low confidence scores")
        
        if emotion_count == 0:
            evaluation["issues"].append("No emotion labels found - emotion processing may have failed")
            evaluation["recommendations"].append("Check emotion model loading and audio quality")
        
        # Check for gaps
        gaps = []
        for i in range(1, len(segments)):
            gap = segments[i]['start_time'] - segments[i-1]['end_time']
            if gap > 5.0:  # 5 second gap
                gaps.append((segments[i-1]['end_time'], segments[i]['start_time'], gap))
        
        if gaps:
            evaluation["issues"].append(f"Found {len(gaps)} significant gaps in transcription")
            evaluation["quality_metrics"]["transcript_gaps"] = gaps[:5]  # First 5 gaps
    
    return evaluation


def evaluate_schema_b(schema_path: Path) -> dict:
    """Evaluate Schema B (Speaker Diarization) quality"""
    evaluation = {
        "exists": schema_path.exists(),
        "quality_metrics": {},
        "issues": [],
        "recommendations": []
    }
    
    if not schema_path.exists():
        evaluation["issues"].append("Schema B file not found - speaker diarization was skipped")
        evaluation["recommendations"].append("Set HF_TOKEN environment variable for speaker diarization")
        evaluation["recommendations"].append("Run: export HF_TOKEN=your_huggingface_token")
        return evaluation
    
    with open(schema_path, 'r') as f:
        schema_b = json.load(f)
    
    segments = schema_b.get('segments', [])
    
    evaluation["quality_metrics"]["num_speakers"] = schema_b.get('num_speakers', 0)
    evaluation["quality_metrics"]["total_segments"] = len(segments)
    
    if segments:
        # Speaker distribution
        speaker_counts = {}
        speaker_durations = {}
        for seg in segments:
            speaker = seg['speaker_id']
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            duration = seg['end_time'] - seg['start_time']
            speaker_durations[speaker] = speaker_durations.get(speaker, 0) + duration
        
        evaluation["quality_metrics"]["speaker_distribution"] = speaker_counts
        evaluation["quality_metrics"]["speaker_time_distribution"] = {
            k: round(v, 2) for k, v in speaker_durations.items()
        }
        
        # Check for issues
        if len(speaker_counts) == 1:
            evaluation["issues"].append("Only one speaker detected - may need tuning")
            evaluation["recommendations"].append("Adjust min_speakers parameter or check audio quality")
    
    return evaluation


def evaluate_schema_c(schema_path: Path) -> dict:
    """Evaluate Schema C (Visual Character Detection) quality"""
    evaluation = {
        "exists": schema_path.exists(),
        "quality_metrics": {},
        "issues": [],
        "recommendations": []
    }
    
    if not schema_path.exists():
        evaluation["issues"].append("Schema C file not found")
        return evaluation
    
    with open(schema_path, 'r') as f:
        schema_c = json.load(f)
    
    characters = schema_c.get('characters', {})
    detections = schema_c.get('detections', [])
    
    evaluation["quality_metrics"]["num_characters"] = len(characters)
    evaluation["quality_metrics"]["total_detections"] = len(detections)
    evaluation["quality_metrics"]["fps"] = schema_c.get('fps', 0)
    evaluation["quality_metrics"]["total_frames"] = schema_c.get('total_frames', 0)
    
    if characters:
        # Character analysis
        char_info = []
        for char_id, char_data in characters.items():
            char_info.append({
                "id": char_id,
                "appearances": char_data.get('num_appearances', 0),
                "first_appearance": char_data.get('first_appearance', 0),
                "last_appearance": char_data.get('last_appearance', 0),
                "time_span": char_data.get('last_appearance', 0) - char_data.get('first_appearance', 0)
            })
        
        # Sort by appearances
        char_info.sort(key=lambda x: x['appearances'], reverse=True)
        evaluation["quality_metrics"]["character_details"] = char_info[:5]  # Top 5 characters
        
        # Time coverage analysis
        if detections:
            detection_times = [d['timestamp'] for d in detections]
            evaluation["quality_metrics"]["first_detection_time"] = min(detection_times)
            evaluation["quality_metrics"]["last_detection_time"] = max(detection_times)
            evaluation["quality_metrics"]["detection_time_coverage"] = max(detection_times) - min(detection_times)
        
        # Issues
        first_detection = min(d['timestamp'] for d in detections) if detections else 0
        if first_detection > 100:  # First detection after 100 seconds
            evaluation["issues"].append(f"First character detection at {first_detection:.1f}s - missing early video content")
            evaluation["recommendations"].append("Process more frames from the beginning of the video")
            evaluation["recommendations"].append("Check if video has black screens or intro sequences")
        
        if len(characters) > 20:
            evaluation["issues"].append(f"Too many characters detected ({len(characters)}) - may have false positives")
            evaluation["recommendations"].append("Increase min_appearances threshold")
            evaluation["recommendations"].append("Tune face detection confidence threshold")
    else:
        evaluation["issues"].append("No characters detected")
        evaluation["recommendations"].append("Check video quality and face visibility")
        evaluation["recommendations"].append("Lower detection confidence threshold")
    
    return evaluation


def evaluate_schema_d(schema_path: Path) -> dict:
    """Evaluate Schema D (Character-Dialogue Matching) quality"""
    evaluation = {
        "exists": schema_path.exists(),
        "quality_metrics": {},
        "issues": [],
        "recommendations": []
    }
    
    if not schema_path.exists():
        evaluation["issues"].append("Schema D file not found")
        return evaluation
    
    with open(schema_path, 'r') as f:
        schema_d = json.load(f)
    
    matches = schema_d.get('matches', [])
    unmatched = schema_d.get('unmatched_dialogues', [])
    
    total_dialogues = len(matches) + len(unmatched)
    evaluation["quality_metrics"]["total_dialogues"] = total_dialogues
    evaluation["quality_metrics"]["matched_dialogues"] = len(matches)
    evaluation["quality_metrics"]["unmatched_dialogues"] = len(unmatched)
    evaluation["quality_metrics"]["match_rate"] = len(matches) / total_dialogues if total_dialogues > 0 else 0
    
    if matches:
        # Confidence analysis
        confidence_scores = []
        for match in matches:
            if 'matching_score' in match and 'final_score' in match['matching_score']:
                confidence_scores.append(match['matching_score']['final_score'])
        
        if confidence_scores:
            evaluation["quality_metrics"]["avg_match_confidence"] = statistics.mean(confidence_scores)
            evaluation["quality_metrics"]["min_match_confidence"] = min(confidence_scores)
            evaluation["quality_metrics"]["max_match_confidence"] = max(confidence_scores)
        
        # Character distribution
        char_counts = {}
        for match in matches:
            char_id = match.get('character_id', 'unknown')
            char_counts[char_id] = char_counts.get(char_id, 0) + 1
        
        evaluation["quality_metrics"]["character_dialogue_distribution"] = char_counts
    else:
        evaluation["issues"].append("No dialogues were matched to characters")
        evaluation["recommendations"].append("Check temporal alignment between audio and visual processing")
        evaluation["recommendations"].append("Ensure characters are detected during dialogue timestamps")
        evaluation["recommendations"].append("Enable speaker diarization for better matching")
        evaluation["recommendations"].append("Lower matching confidence threshold")
    
    # Specific issue for 0% match rate
    if evaluation["quality_metrics"]["match_rate"] == 0:
        evaluation["issues"].append("CRITICAL: 0% dialogue-character match rate")
        evaluation["recommendations"].append("Primary issue: Character detections start too late in video")
        evaluation["recommendations"].append("Process more frames, especially from early parts of video")
    
    return evaluation


def generate_evaluation_report(session_dir: Path) -> dict:
    """Generate comprehensive evaluation report for a pipeline session"""
    report = {
        "session": session_dir.name,
        "evaluation_time": datetime.now().isoformat(),
        "schemas": {},
        "overall_issues": [],
        "overall_recommendations": []
    }
    
    # Find output directories
    audio_dir = list(session_dir.glob("audio_output/*"))
    if audio_dir:
        audio_dir = audio_dir[0]
        
        # Evaluate Schema A
        schema_a_path = audio_dir / "schemas" / "schema_a_transcription.json"
        schema_a_emotions_path = audio_dir / "schemas" / "schema_a_with_emotions.json"
        
        if schema_a_emotions_path.exists():
            report["schemas"]["schema_a"] = evaluate_schema_a(schema_a_emotions_path)
        else:
            report["schemas"]["schema_a"] = evaluate_schema_a(schema_a_path)
        
        # Evaluate Schema B
        schema_b_path = audio_dir / "schemas" / "schema_b_speakers.json"
        report["schemas"]["schema_b"] = evaluate_schema_b(schema_b_path)
    
    # Evaluate Schema C
    visual_dir = session_dir / "visual_output"
    if visual_dir.exists():
        schema_c_path = visual_dir / "character_data_schemaC.json"
        report["schemas"]["schema_c"] = evaluate_schema_c(schema_c_path)
    
    # Evaluate Schema D
    fusion_dir = session_dir / "fusion_output"
    if fusion_dir.exists():
        schema_d_path = fusion_dir / "schema_d_matches.json"
        report["schemas"]["schema_d"] = evaluate_schema_d(schema_d_path)
    
    # Overall analysis
    if not report["schemas"].get("schema_b", {}).get("exists"):
        report["overall_issues"].append("Speaker diarization was skipped - reduces matching accuracy")
        report["overall_recommendations"].append("Enable speaker diarization by setting HF_TOKEN")
    
    # Check temporal alignment
    if "schema_a" in report["schemas"] and "schema_c" in report["schemas"]:
        schema_a_metrics = report["schemas"]["schema_a"]["quality_metrics"]
        schema_c_metrics = report["schemas"]["schema_c"]["quality_metrics"]
        
        if schema_a_metrics.get("first_speech_time", 0) < 50 and schema_c_metrics.get("first_detection_time", 999) > 100:
            report["overall_issues"].append("Significant temporal mismatch: Dialogue starts early but character detection starts late")
            report["overall_recommendations"].append("Process frames uniformly throughout video, not just later portions")
    
    return report


def print_evaluation_report(report: dict):
    """Print evaluation report in readable format"""
    print("\n" + "="*70)
    print(f"PIPELINE OUTPUT EVALUATION REPORT")
    print(f"Session: {report['session']}")
    print(f"Time: {report['evaluation_time']}")
    print("="*70)
    
    # Schema evaluations
    for schema_name, evaluation in report["schemas"].items():
        print(f"\n{schema_name.upper()} Evaluation:")
        print("-" * 50)
        
        if not evaluation["exists"]:
            print(f"❌ {schema_name.upper()} NOT FOUND")
        else:
            print(f"✅ {schema_name.upper()} exists")
            
            # Quality metrics
            print("\nQuality Metrics:")
            for metric, value in evaluation["quality_metrics"].items():
                if isinstance(value, dict):
                    print(f"  {metric}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                elif isinstance(value, float):
                    print(f"  {metric}: {value:.2f}")
                else:
                    print(f"  {metric}: {value}")
        
        # Issues
        if evaluation["issues"]:
            print("\nIssues Found:")
            for issue in evaluation["issues"]:
                print(f"  ⚠️  {issue}")
        
        # Recommendations
        if evaluation["recommendations"]:
            print("\nRecommendations:")
            for rec in evaluation["recommendations"]:
                print(f"  💡 {rec}")
    
    # Overall assessment
    print("\n" + "="*70)
    print("OVERALL ASSESSMENT")
    print("="*70)
    
    if report["overall_issues"]:
        print("\nCritical Issues:")
        for issue in report["overall_issues"]:
            print(f"  🔴 {issue}")
    
    if report["overall_recommendations"]:
        print("\nKey Recommendations:")
        for rec in report["overall_recommendations"]:
            print(f"  ⭐ {rec}")
    
    # Save detailed report
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate pipeline output quality")
    parser.add_argument("session_dir", help="Path to pipeline session directory")
    parser.add_argument("--save-json", help="Save evaluation report as JSON")
    
    args = parser.parse_args()
    
    session_path = Path(args.session_dir)
    if not session_path.exists():
        print(f"Error: Session directory not found: {session_path}")
        sys.exit(1)
    
    # Generate evaluation
    report = generate_evaluation_report(session_path)
    
    # Print report
    print_evaluation_report(report)
    
    # Save if requested
    if args.save_json:
        with open(args.save_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nEvaluation report saved to: {args.save_json}")


if __name__ == "__main__":
    main()