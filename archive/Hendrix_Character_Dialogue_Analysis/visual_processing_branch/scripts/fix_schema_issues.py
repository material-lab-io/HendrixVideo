#!/usr/bin/env python3
"""
Fix Schema Issues Script

This script fixes known issues in existing schema files:
1. Removes segments with 0 duration or empty text from Schema A
2. Ensures all required fields are present in Schema C
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
import shutil
from datetime import datetime


def fix_schema_a(schema_path: Path) -> int:
    """Fix Schema A issues (0 duration segments, empty text)"""
    print(f"\nFixing Schema A: {schema_path}")
    
    # Backup original
    backup_path = schema_path.with_suffix('.json.backup')
    shutil.copy2(schema_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    original_count = len(data.get('segments', []))
    fixed_segments = []
    removed_count = 0
    
    # Filter out problematic segments
    for i, seg in enumerate(data.get('segments', [])):
        duration = seg.get('end_time', 0) - seg.get('start_time', 0)
        text = seg.get('text', '').strip()
        
        if duration <= 0:
            print(f"  Removing segment {i}: zero/negative duration ({duration}s)")
            removed_count += 1
            continue
            
        if not text:
            print(f"  Removing segment {i}: empty text")
            removed_count += 1
            continue
            
        fixed_segments.append(seg)
    
    # Update segments
    data['segments'] = fixed_segments
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['schema_fixed'] = datetime.now().isoformat()
    data['metadata']['segments_removed'] = removed_count
    
    # Save fixed schema
    with open(schema_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Fixed: Removed {removed_count} segments, {len(fixed_segments)} remaining")
    return removed_count


def fix_schema_c(schema_path: Path) -> int:
    """Fix Schema C issues (ensure all required fields)"""
    print(f"\nFixing Schema C: {schema_path}")
    
    # Backup original
    backup_path = schema_path.with_suffix('.json.backup')
    shutil.copy2(schema_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    with open(schema_path, 'r') as f:
        data = json.load(f)
    
    fixes_made = 0
    
    # Ensure all characters have required fields
    characters = data.get('characters', {})
    for char_id, char_data in characters.items():
        # Check for required fields
        if 'num_appearances' not in char_data:
            # Count appearances from detections
            appearances = sum(1 for d in data.get('detections', []) 
                            if d.get('character_id') == char_id)
            char_data['num_appearances'] = appearances
            fixes_made += 1
            print(f"  Added num_appearances for character {char_id}: {appearances}")
        
        if 'appearance_segments' not in char_data:
            char_data['appearance_segments'] = []
            fixes_made += 1
            print(f"  Added empty appearance_segments for character {char_id}")
        
        # Ensure other fields have defaults
        if 'representative_embeddings' not in char_data:
            char_data['representative_embeddings'] = []
        if 'attributes' not in char_data:
            char_data['attributes'] = None
        if 'description' not in char_data:
            char_data['description'] = None
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['schema_fixed'] = datetime.now().isoformat()
    data['metadata']['fixes_applied'] = fixes_made
    
    # Save fixed schema
    with open(schema_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Fixed: Applied {fixes_made} fixes")
    return fixes_made


def fix_session(session_dir: Path) -> Dict:
    """Fix all schemas in a session"""
    print(f"\n{'='*60}")
    print(f"Fixing schemas in session: {session_dir.name}")
    print(f"{'='*60}")
    
    results = {
        'session': session_dir.name,
        'fixes': {}
    }
    
    # Fix Schema A
    audio_dirs = list((session_dir / "audio_output").glob("*"))
    if audio_dirs:
        schema_a_path = audio_dirs[0] / "schemas" / "schema_a_transcription.json"
        if schema_a_path.exists():
            removed = fix_schema_a(schema_a_path)
            results['fixes']['schema_a'] = {
                'path': str(schema_a_path),
                'segments_removed': removed
            }
        else:
            print(f"\nSchema A not found: {schema_a_path}")
    
    # Fix Schema C
    schema_c_path = session_dir / "visual_output" / "character_data_schemaC.json"
    if schema_c_path.exists():
        fixes = fix_schema_c(schema_c_path)
        results['fixes']['schema_c'] = {
            'path': str(schema_c_path),
            'fixes_applied': fixes
        }
    else:
        print(f"\nSchema C not found: {schema_c_path}")
    
    print(f"\n{'='*60}")
    print("Schema fixes complete!")
    print(f"{'='*60}")
    
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_schema_issues.py <session_directory>")
        print("       python fix_schema_issues.py --all <output_directory>")
        sys.exit(1)
    
    if sys.argv[1] == "--all" and len(sys.argv) >= 3:
        # Fix all sessions in output directory
        output_dir = Path(sys.argv[2])
        if not output_dir.exists():
            print(f"Error: Output directory not found: {output_dir}")
            sys.exit(1)
        
        # Find all session directories
        sessions = []
        for subdir in output_dir.iterdir():
            if subdir.is_dir():
                session_dirs = list(subdir.glob("session_*"))
                sessions.extend(session_dirs)
        
        print(f"Found {len(sessions)} sessions to fix")
        
        for session_dir in sessions:
            fix_session(session_dir)
    else:
        # Fix single session
        session_dir = Path(sys.argv[1])
        if not session_dir.exists():
            print(f"Error: Session directory not found: {session_dir}")
            sys.exit(1)
        
        fix_session(session_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())