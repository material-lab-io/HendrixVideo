# Pipeline Output Files Guide

## Directory Structure
When you run the pipeline, it creates a session directory with this structure:
```
output/<pipeline_name>/session_YYYYMMDD_HHMMSS/
├── audio_output/
│   └── <video_name>_YYYYMMDD_HHMMSS/
│       └── schemas/
│           ├── schema_a_transcription.json
│           └── schema_b_speakers.json
├── visual_output/
│   ├── character_data_schemaC.json
│   ├── tracking_data.json
│   ├── visual_pipeline_report.txt
│   ├── lip_movement_data.pkl
│   ├── extraction_stats.json
│   └── extracted_frames/ (if saved)
└── fusion_output/
    ├── schema_d_matches.json
    ├── optimized_matching_report.md (or fusion_report.md)
    └── character_profiles.json (if using advanced matcher)

# Scene-aware pipeline adds:
├── scene_data/
│   └── detected_scenes.json          # Scene boundaries and statistics
├── visual_output/
│   ├── scene_clustering_results.json # Scene-based character clustering
│   └── character_data_schemaC_scenes.json # Enhanced with scene_id
└── fusion_output/
    └── scene_aware_matching_report.md # Scene-aware analysis
```

## Key Files to Check Manually

### 1. **Quick Overview Reports** (Start Here!)

#### `fusion_output/optimized_matching_report.md`
- **What it shows**: Human-readable summary of results
- **Key info**: Match rate, character statistics, sample matches, confidence scores
- **Best for**: Getting a quick understanding of pipeline performance

#### `visual_output/visual_pipeline_report.txt`
- **What it shows**: Character detection summary
- **Key info**: Number of characters, their appearance times, track IDs
- **Best for**: Understanding who was detected in the video

### 2. **Detailed JSON Schemas** (For Deep Analysis)

#### `fusion_output/schema_d_matches.json`
- **What it shows**: Final character-dialogue matches
- **Key sections**:
  - `matches[]`: All successful character-dialogue pairs
  - `unmatched_dialogues[]`: Dialogues that couldn't be matched
  - Each match includes:
    - `character_id`: Which character spoke
    - `dialogue.text`: What was said
    - `dialogue.start_time/end_time`: When it was said
    - `matching_score.final_score`: How confident the match is
- **Best for**: Analyzing individual matches and their confidence

#### `audio_output/.../schemas/schema_a_transcription.json`
- **What it shows**: All transcribed dialogue
- **Key sections**:
  - `segments[]`: Each dialogue with text, timing, emotion
  - `metadata`: Processing details
- **Best for**: Checking transcription quality and emotions

#### `visual_output/character_data_schemaC.json`
- **What it shows**: All detected characters and their appearances
- **Key sections**:
  - `characters{}`: Character profiles with embeddings
  - `detections[]`: Every face detection with timestamp
- **Best for**: Understanding character presence in video

### 3. **Validation and Statistics**

#### `extraction_stats.json`
- **What it shows**: Frame extraction statistics
- **Key info**: Strategy used, frames extracted, quality metrics
- **Best for**: Understanding visual processing quality

#### `schema_validation_report.json` (if you run validation)
- **What it shows**: Validation results for all schemas
- **Key info**: Which schemas are valid, any errors found
- **Best for**: Ensuring data integrity

## Example Commands to View Files

### View matching report (human-readable):
```bash
cat output/optimized_robust/session_20250803_112322/fusion_output/optimized_matching_report.md
```

### View character-dialogue matches (with jq for pretty JSON):
```bash
# Show match statistics
jq '.matching_summary' output/.../fusion_output/schema_d_matches.json

# Show first 5 matches with character and dialogue
jq '.matches[:5] | .[] | {character: .character_id, text: .dialogue.text, confidence: .matching_score.final_score}' output/.../fusion_output/schema_d_matches.json

# Show all unmatched dialogues
jq '.unmatched_dialogues[] | {text: .text, time: .start_time}' output/.../fusion_output/schema_d_matches.json
```

### View character summary:
```bash
# Show character list with appearance counts
jq '.characters | to_entries | .[] | {id: .key, appearances: .value.num_appearances, screen_time: .value.total_screen_time}' output/.../visual_output/character_data_schemaC.json
```

### View transcription with emotions:
```bash
# Show first 10 dialogues with emotions
jq '.segments[:10] | .[] | {text: .text, emotion: .emotion, confidence: .confidence}' output/.../audio_output/.../schemas/schema_a_transcription.json
```

## Scene-Aware Pipeline Files (NEW!)

### View detected scenes:
```bash
# Show scene boundaries
jq '.scenes[] | {scene_id: .scene_id, start: .start_time, end: .end_time, duration: .duration}' output/.../scene_data/detected_scenes.json

# Count scenes
jq '.total_scenes' output/.../scene_data/detected_scenes.json
```

### View scene clustering results:
```bash
# Show global characters after scene-aware clustering
jq '.global_characters[] | {id: .character_id, scenes: .scenes, total_detections: .total_detections}' output/.../visual_output/scene_clustering_results.json

# Show clustering statistics
jq '.statistics' output/.../visual_output/scene_clustering_results.json
```

### Check character scene appearances:
```bash
# Show which scenes each character appears in
jq '.characters | to_entries | .[] | {character: .key, scenes: .value.scene_appearances}' output/.../visual_output/character_data_schemaC_scenes.json
```

## Real Example Paths

For the Sintel trailer test:
```bash
# Main report
cat output/optimized_robust/session_20250803_112322/fusion_output/optimized_matching_report.md

# Character-dialogue matches
cat output/optimized_robust/session_20250803_112322/fusion_output/schema_d_matches.json

# Transcription
cat output/optimized_robust/session_20250803_112322/audio_output/sintel_trailer_20250803_112327/schemas/schema_a_transcription.json

# Characters
cat output/optimized_robust/session_20250803_112322/visual_output/character_data_schemaC.json
```

## Quick Python Script to Explore Results

```python
import json

# Load the main results
with open('path/to/schema_d_matches.json') as f:
    matches = json.load(f)

# Print summary
print(f"Total matches: {len(matches['matches'])}")
print(f"Match rate: {matches['matching_summary']['match_rate']*100:.1f}%")

# Show character dialogue distribution
from collections import Counter
char_counts = Counter(m['character_id'] for m in matches['matches'])
print("\nCharacter dialogue counts:")
for char_id, count in char_counts.most_common():
    print(f"  Character {char_id}: {count} dialogues")

# Show some actual matches
print("\nSample matches:")
for match in matches['matches'][:5]:
    print(f"\nCharacter {match['character_id']} says:")
    print(f"  \"{match['dialogue']['text']}\"")
    print(f"  Time: {match['dialogue']['start_time']:.1f}s")
    print(f"  Confidence: {match['matching_score']['final_score']:.3f}")
```

## Tips for Manual Review

1. **Start with the markdown report** in fusion_output - it's the most readable
2. **Check unmatched dialogues** to understand what didn't work
3. **Look at confidence scores** - matches below 0.5 might need review
4. **Compare speaker IDs** (Schema B) with character IDs to see patterns
5. **Use visual_pipeline_report.txt** to quickly see which characters were found

The most important file for manual checking is **`fusion_output/optimized_matching_report.md`** or **`fusion_output/schema_d_matches.json`** as they contain the final results of who said what.