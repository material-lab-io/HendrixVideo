# Comprehensive Video Captioning System

A multi-modal video captioning system that generates rich narrative captions by fusing audio analysis (dialogue, emotions, speakers) with visual scene analysis using LLaVA-NeXT (LLaVA 1.6).

## 🎯 Features

- **Multi-modal Fusion**: Combines audio transcriptions, speaker identification, emotion detection, and visual scene descriptions
- **Character-aware Captions**: Integrates character identification with dialogue attribution
- **Emotion Context**: Includes emotional states (angry, sad, happy, etc.) in narrative captions
- **Scene Continuity**: Maintains narrative flow across scenes with context management
- **Multiple Output Formats**: JSON, SRT, WebVTT, HTML, and plain text
- **Improved Templates**: Enhanced prompt templates for concise, natural language output

## 📋 Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- ~8GB disk space for LLaVA model
- Audio analysis output (from companion audio_analysis system)
- Scene analysis output (from Hendrix_Video_Analysis system)

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/comprehensive_captioning.git
cd comprehensive_captioning
```

### 2. Install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the pipeline
```bash
# Basic usage
./run_pipeline.sh

# Or with custom paths
python scripts/generate_comprehensive_captions.py \
  --audio-analysis /path/to/audio_analysis/output/session_* \
  --scene-analysis /path/to/scenes.json \
  --keyframes /path/to/keyframes/ \
  --output-dir ./output/my_captions
```

## 📁 Input Data Structure

### Audio Analysis Output
```
session_*/
├── audio_output/
│   └── */schemas/
│       ├── schema_a_transcription.json  # Dialogue with emotions
│       └── schema_b_speakers.json       # Speaker diarization
├── visual_output/
│   └── character_data_schemaC.json      # Character detections
└── fusion_output/
    └── schema_d_matches.json            # Character-dialogue matches
```

### Scene Analysis Output
```json
{
  "total_scenes": 138,
  "scenes": [{
    "scene_id": 1,
    "start_time": 0.0,
    "end_time": 8.875,
    "summary": "Visual description of the scene"
  }]
}
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐
│ Audio Analysis  │     │ Scene Analysis   │
│ (Schemas A-D)   │     │ (scenes.json)    │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────────┐
              │ Data Fusion     │
              │ Engine          │
              └──────┬──────────┘
                     │
              ┌──────▼──────────┐     ┌─────────────┐
              │ Context Packets │────►│ LLaVA-NeXT  │
              └─────────────────┘     │ (MLLM)      │
                                      └──────┬──────┘
                                             │
                                      ┌──────▼──────────┐
                                      │ Caption         │
                                      │ Generator       │
                                      └──────┬──────────┘
                                             │
                                      ┌──────▼──────────┐
                                      │ Output          │
                                      │ Formatter       │
                                      └──────┬──────────┘
                                             │
                                  ┌──────────┴───────────┐
                                  │ JSON│SRT│VTT│HTML│TXT│
                                  └─────────────────────┘
```

## ⚙️ Configuration

Edit `config/captioning_config.yaml` to customize:

```yaml
# Model settings
mllm:
  provider: llava  # or openai, mock
  model: llava-hf/llava-v1.6-vicuna-7b-hf
  generation:
    temperature: 0.7
    max_tokens: 150  # Reduced for conciseness

# Prompt settings
prompt:
  template: narrative_with_emotions
  use_improved_templates: true  # Enable enhanced templates

# Output settings
output:
  formats: [json, srt, webvtt, html]
```

## 📊 Output Formats

### JSON
```json
{
  "captions": [{
    "caption_id": "SCENE_CAP_001",
    "scene_id": 1,
    "start_time": 0.0,
    "end_time": 8.875,
    "caption": "In a stark black and white world...",
    "characters": ["Character_1"],
    "has_dialogue": true
  }]
}
```

### SRT/WebVTT
```
1
00:00:00,000 --> 00:00:08,875
[Character_1] In a stark black and white world, character_1, filled with anger, bellows, "4, 3, 2, 1, GO!" as they push forward into the darkness.
```

## 🔧 Advanced Usage

### Custom Prompt Templates
```python
from comprehensive_captioning.prompt_templates_improved import ImprovedPromptTemplate

class MyCustomTemplate(ImprovedPromptTemplate):
    def generate_prompt(self, context):
        # Your custom prompt logic
        return prompt
```

### Batch Processing
```bash
# Process only first N scenes
python scripts/generate_comprehensive_captions.py \
  --audio-analysis /path/to/audio \
  --scene-analysis /path/to/scenes.json \
  --output-dir ./output \
  --max-scenes 10
```

### Evaluation
```bash
# Compare original vs improved captions
python evaluate_improvements.py
```

## 📈 Performance

- **Processing Time**: ~6-8 seconds per scene with keyframes
- **GPU Memory**: ~6GB with LLaVA 7B model
- **Caption Length**: Average 37 words (reduced from 102)
- **Quality Metrics**:
  - 100% elimination of repetitive template phrases
  - 52% increase in dialogue quote integration
  - 63% reduction in average caption length

## 🛠️ Troubleshooting

### GPU Out of Memory
```bash
# Force CPU mode
CUDA_VISIBLE_DEVICES="" python scripts/generate_comprehensive_captions.py ...
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Path Issues
- Use absolute paths for input directories
- Ensure audio analysis session folders match the pattern

## 📝 Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint
flake8 . --max-line-length=120
```

### Adding New MLLM Providers
1. Inherit from `MLLMInterface` in `caption_generator.py`
2. Implement `generate_caption()` and `is_available()`
3. Register in `create_mllm_interface()`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- LLaVA team for the excellent multi-modal model
- OpenAI for GPT-4 support
- Contributors to the audio and video analysis pipelines

## 📚 Citation

If you use this system in your research, please cite:

```bibtex
@software{comprehensive_captioning,
  title = {Comprehensive Video Captioning System},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/comprehensive_captioning}
}
```