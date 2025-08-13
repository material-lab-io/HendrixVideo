# Audio Processing Branch

This branch contains all components for audio processing in the Character-Dialogue Analysis pipeline.

## Directory Structure

```
audio_processing_branch/
├── src/
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── whisper_processor.py      # Whisper ASR for transcription
│   │   ├── emotion_processor.py      # wav2vec2 emotion recognition (FIXED!)
│   │   └── diarization_processor.py  # Pyannote speaker diarization
│   └── schemas.py                    # Schema A and B definitions
├── scripts/
│   ├── complete_audio_pipeline.py    # Main pipeline orchestrator
│   ├── test_whisper_component.py     # Test Whisper individually
│   ├── test_emotion_component.py     # Test emotion recognition
│   ├── test_diarization_component.py # Test speaker diarization
│   ├── test_complete_pipeline.py     # Test full pipeline
│   ├── test_whisper_youtube.py       # Test with YouTube videos
│   ├── analyze_results.py            # Analyze transcription results
│   ├── analyze_emotions.py           # Analyze emotion distribution
│   ├── analyze_diarization.py        # Analyze speaker patterns
│   ├── setup_models.py               # Download required models
│   └── test_setup.py                 # Verify installation
├── tests/                            # Unit tests (to be added)
├── docs/                             # Documentation
├── requirements.txt                  # Python dependencies
├── .env                             # Environment configuration
└── .gitignore                       # Git ignore rules
```

## Components

### 1. Whisper Processor (`src/audio/whisper_processor.py`)
- Transcribes audio using OpenAI Whisper
- Supports multiple model sizes (tiny, base, small, medium, large, large-v3)
- Generates Schema A with timestamps and confidence scores

### 2. Emotion Processor (`src/audio/emotion_processor.py`) - **FIXED!**
- Adds emotion labels to transcription segments
- Uses wav2vec2-large-superb-er model
- Detects 7 emotions: angry, happy, sad, surprise, fear, disgust, neutral
- **Status**: ✅ Working properly after recent fixes

### 3. Diarization Processor (`src/audio/diarization_processor.py`)
- Identifies different speakers in audio
- Uses pyannote/speaker-diarization-3.1
- Generates Schema B with speaker segments

## Usage

### Complete Pipeline
```bash
cd audio_processing_branch
python scripts/complete_audio_pipeline.py video.mp4 --whisper-model large-v3
```

### Individual Components
```bash
# Test Whisper only
python scripts/test_whisper_component.py video.mp4

# Test emotion recognition (NOW WORKING!)
python scripts/test_emotion_component.py video.mp4

# Test speaker diarization
python scripts/test_diarization_component.py video.mp4
```

### Analysis Tools
```bash
# Analyze results
python scripts/analyze_results.py output/pipeline/*/schemas/schema_a_with_emotions.json

# Analyze emotions
python scripts/analyze_emotions.py output/pipeline/*/schemas/schema_a_with_emotions.json

# Analyze speakers
python scripts/analyze_diarization.py output/pipeline/*/schemas/schema_b_speakers.json
```

## Output Schemas

### Schema A (Transcription + Emotions)
```json
{
  "video_id": "example",
  "segments": [{
    "segment_id": "SEG_0001",
    "text": "transcribed text",
    "start_time": 0.0,
    "end_time": 2.5,
    "confidence": 0.98,
    "emotion": "happy",
    "emotion_confidence": 0.75
  }]
}
```

### Schema B (Speaker Diarization)
```json
{
  "video_id": "example",
  "speakers": ["SPEAKER_00", "SPEAKER_01"],
  "segments": [{
    "speaker_id": "SPEAKER_00",
    "start_time": 0.0,
    "end_time": 5.2,
    "confidence": 0.89
  }]
}
```

## Environment Setup

1. Activate the shared virtual environment from root:
```bash
# From audio_processing_branch directory:
source ../venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
HF_TOKEN=your_huggingface_token  # Required for pyannote
TF_USE_LEGACY_KERAS=1            # Required for emotion processing
```

4. Verify installation:
```bash
python scripts/test_setup.py
```

## Performance

- Whisper large-v3: ~0.12x realtime (3 min for 25-min video)
- Emotion recognition: ~30s for 25-min video (✅ Working)
- Speaker diarization: ~28s for 25-min video
- Total pipeline: ~4 min for 25-min video

## Recent Improvements

1. **Fixed Emotion Processing**: Model now loads correctly and outputs emotions
2. **Better Error Handling**: Pipeline continues even if components fail
3. **Environment Variable Support**: Auto-loads from .env file
4. **Progress Reporting**: Better feedback during processing

## Common Issues

1. **Missing Emotions**: Ensure TF_USE_LEGACY_KERAS=1 is set
2. **Diarization Skipped**: Check HF_TOKEN is set in .env
3. **Memory Errors**: Process shorter video segments
4. **Model Download**: Models auto-download on first use

## Testing

```bash
# Test complete pipeline
python scripts/test_complete_pipeline.py

# Test with sample videos
python scripts/test_whisper_youtube.py

# Verify all components
python scripts/test_setup.py
```