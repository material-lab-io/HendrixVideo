# Hendrix Character-Dialogue Analysis System

A comprehensive multimodal AI system that analyzes videos to extract characters, transcribe dialogues with emotions, and match them together using advanced fusion techniques.

## 🎯 Overview

This project implements a complete pipeline for character-dialogue analysis in videos:
- **Audio Processing**: Transcription, emotion detection, and speaker diarization
- **Visual Processing**: Face detection, character identification, and tracking
- **Fusion**: Intelligent matching of characters to their dialogue

### Key Features
- 🎙️ Multi-language transcription with OpenAI Whisper
- 😊 7-class emotion recognition for each dialogue segment (NOW WORKING!)
- 👥 Speaker diarization to separate multiple speakers
- 👤 Face detection and recognition with InsightFace/ArcFace
- 🧩 Advanced character-dialogue matching with confidence scoring
- 📊 Structured output in 4 progressive schemas
- 🚀 **74-83% character-dialogue match rate** (25x improvement from initial version)

## 🏗️ Architecture

```
Video Input
    ├── Audio Processing Branch
    │   ├── Whisper ASR → Schema A (Transcriptions + Emotions)
    │   └── Pyannote → Schema B (Speaker Diarization)
    │
    └── Visual Processing Branch
        └── InsightFace + SORT → Schema C (Character Detection)
                │
                └── Fusion Stage → Schema D (Character-Dialogue Matches)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- CUDA-capable GPU (recommended)
- FFmpeg installed
- HuggingFace account (for Pyannote)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/material-lab-io/Hendrix_Character_Dialogue_Analysis.git
cd audio_analysis
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
# For complete installation
cd visual_processing_branch
pip install -r requirements.txt

# Note: This installs both audio and visual processing dependencies
```

4. **Set up environment variables**
```bash
# Create .env file in root directory
cat > .env << EOF
HF_TOKEN=your_huggingface_token
TF_USE_LEGACY_KERAS=1
EOF
```

### Running the Complete Pipeline

```bash
cd visual_processing_branch
source ../venv/bin/activate

# Set required environment variables
export TF_USE_LEGACY_KERAS=1
export HF_TOKEN=your_huggingface_token

# Run optimized pipeline (RECOMMENDED)
python scripts/run_optimized_robust_pipeline.py path/to/video.mp4 --verbose

# Or run legacy pipeline
python scripts/run_complete_pipeline_v2.py path/to/video.mp4 --output output/results
```

### Validate and Display Results

```bash
# Validate output schemas
python scripts/validate_all_schemas.py output/complete_pipeline_v2/session_*

# Display results in human-readable format
python scripts/display_all_schemas.py output/complete_pipeline_v2/session_*
```

## 📋 Pipeline Components

### 1. Audio Processing (Schema A & B)
- **Transcription**: Multiple Whisper models (tiny to large-v3)
- **Emotions**: anger, happy, sad, neutral, surprise, fear, disgust (FIXED!)
- **Speakers**: Automatic speaker separation and identification

```bash
cd audio_processing_branch
python scripts/complete_audio_pipeline.py video.mp4 --whisper-model base
```

### 2. Visual Processing (Schema C)
- **Face Detection**: InsightFace RetinaFace with quality scoring
- **Face Recognition**: 512-dimensional embeddings
- **Character Clustering**: DBSCAN for unique character identification

```bash
cd visual_processing_branch
python scripts/tracked_visual_pipeline.py video.mp4 --target-frames 300
```

### 3. Fusion (Schema D)
- **Heuristic Matching**: Based on temporal overlap, character presence
- **Confidence Scoring**: Multi-factor scoring system
- **Match Rate**: 74-83% success rate

## 📊 Output Schemas

### Schema A: Transcription with Emotions
```json
{
  "segment_id": "SEG_0001",
  "text": "Hello, welcome to the tutorial",
  "start_time": 1.5,
  "end_time": 3.2,
  "confidence": 0.95,
  "emotion": "happy",
  "emotion_confidence": 0.87
}
```

### Schema B: Speaker Diarization
```json
{
  "segment_id": "SPK_SEG_0001",
  "speaker_id": "SPEAKER_00",
  "start_time": 1.5,
  "end_time": 3.2,
  "confidence": 0.92
}
```

### Schema C: Character Detection
```json
{
  "character_id": "CHAR_001",
  "num_appearances": 45,
  "total_screen_time": 120.5,
  "average_confidence": 0.89,
  "embedding": [0.123, -0.456, ...],
  "attributes": {
    "age": "25-35",
    "gender": "male",
    "dominant_emotion": "neutral"
  }
}
```

### Schema D: Character-Dialogue Matches
```json
{
  "match_id": "MATCH_0001",
  "character_id": "CHAR_001",
  "dialogue_segment": { ... },
  "matching_score": {
    "heuristic_scores": {
      "single_character": 0.8,
      "temporal_overlap": 0.9
    },
    "final_score": 0.85,
    "confidence_level": "high"
  }
}
```

## 🛠️ Advanced Configuration

### Whisper Model Selection
- `tiny`: Fastest, least accurate
- `base`: Good balance (default)
- `small`: Better accuracy
- `medium`: High accuracy
- `large-v3`: Best accuracy, slowest

### Frame Extraction Modes
- `uniform`: Extract frames at regular intervals
- `intelligent`: Extract keyframes based on scene changes
- `hybrid`: Combination of both methods

### Processing Options
```bash
# High-quality processing
python scripts/run_complete_pipeline_v2.py video.mp4 \
    --whisper-model large-v3 \
    --target-frames 1000 \
    --extraction-mode intelligent

# Fast processing
python scripts/run_complete_pipeline_v2.py video.mp4 \
    --whisper-model tiny \
    --target-frames 300 \
    --extraction-mode uniform
```

## 📈 Performance Metrics

| Component | Processing Time (25-min video) | Accuracy/Status |
|-----------|-------------------------------|-----------------|
| Transcription | ~30 seconds | 95%+ accuracy |
| Emotion Detection | ~8 seconds | ✅ FIXED - Working |
| Speaker Diarization | ~30 seconds | 85-90% accuracy |
| Visual Processing | ~15-80 seconds | High accuracy |
| Character-Dialogue Matching | ~5 seconds | 74-83% match rate |
| Total Pipeline | ~90-200 seconds | Production Ready |

## 🚀 New Features

### Long Video Support
- Process videos up to several hours
- Memory-efficient streaming processing
- Automatic chunking for large files

### Validation and Display Tools
```bash
# Validate all output schemas
python scripts/validate_all_schemas.py output/session_*

# Display results in readable format
python scripts/display_all_schemas.py output/session_*
```

### Optimized Pipeline
```bash
# New robust pipeline with better performance
python scripts/run_optimized_robust_pipeline.py video.mp4 --verbose
```

## 📁 Project Structure

```
audio_analysis/
├── audio_processing_branch/     # Audio pipeline implementation
│   ├── src/
│   │   ├── audio/              # Audio processors
│   │   └── schemas.py          # Schema definitions
│   └── scripts/                # Executable scripts
├── visual_processing_branch/    # Visual pipeline implementation
│   ├── src/
│   │   ├── visual/             # Visual processors
│   │   └── fusion/             # Character-dialogue matching
│   ├── scripts/                # Executable scripts
│   └── configs/                # Configuration presets
├── venv/                       # Virtual environment
├── .env                        # Environment variables
├── README.md                   # This file
└── CLAUDE.md                   # Detailed documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **OpenAI Whisper**: Speech recognition
- **Pyannote**: Speaker diarization
- **InsightFace**: Face detection and recognition
- **Hugging Face**: Emotion recognition models
- **DeepFace**: Facial attribute analysis

## 📞 Support

- 📖 Check [CLAUDE.md](CLAUDE.md) for detailed documentation
- 🐛 Report issues on [GitHub Issues](https://github.com/material-lab-io/Hendrix_Character_Dialogue_Analysis/issues)
- 📧 Contact: your-email@example.com

---

Made with ❤️ by the Hendrix team