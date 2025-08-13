# Speaker Diarization Guide for Hendrix Pipeline

## Overview

Speaker diarization is the process of identifying "who spoke when" in an audio/video file. The Hendrix Character-Dialogue Analysis pipeline uses speaker diarization to enhance character-dialogue matching accuracy.

## Current Implementation

The pipeline now includes a **flexible diarization system** that works with or without authentication:

### 1. **Pyannote (Primary - Best Quality)**
- Requires HuggingFace token
- State-of-the-art accuracy
- Real-time factor ~2.5% on GPU

### 2. **Simple-Diarizer (Alternative - No Auth)**
- No authentication required
- Uses SpeechBrain models
- Slightly lower accuracy but fully functional

### 3. **No Diarization (Fallback)**
- Pipeline works without speaker data
- Uses only visual and timing information
- Reduced accuracy in multi-speaker scenarios

## Setup Options

### Option 1: Enable Pyannote (Recommended)

1. Create a free HuggingFace account at https://huggingface.co
2. Generate token at https://huggingface.co/settings/tokens
3. Accept terms at https://huggingface.co/pyannote/speaker-diarization-3.1
4. Set environment variable:
   ```bash
   export HF_TOKEN=your_token_here
   ```

### Option 2: Use Simple-Diarizer (No Auth)

1. Install simple-diarizer:
   ```bash
   pip install simple-diarizer
   ```

2. The pipeline will automatically use it when available

### Option 3: Run Without Diarization

No setup needed - the pipeline automatically works without speaker diarization if no backend is available.

## How It Works

The `FlexibleDiarizationProcessor` automatically selects the best available backend:

1. **With HF_TOKEN**: Uses Pyannote for best quality
2. **Without HF_TOKEN but with simple-diarizer**: Uses Simple-Diarizer
3. **Neither available**: Creates empty Schema B, pipeline continues

## Impact on Results

### With Speaker Diarization:
- More accurate character-dialogue matching
- Speaker voice patterns help identify characters
- Better handling of off-screen dialogue

### Without Speaker Diarization:
- Character matching based on visual presence and timing
- Still functional but may miss some matches
- Works well for simple videos with clear on-screen speakers

## Configuration

The pipeline automatically handles all configurations. You can specify preferences:

```bash
# Force specific number of speakers
python scripts/complete_audio_pipeline.py video.mp4 --num-speakers 2

# Or let it auto-detect
python scripts/complete_audio_pipeline.py video.mp4
```

## Performance Comparison

| Backend | Auth Required | Accuracy | Speed | GPU Support |
|---------|--------------|----------|-------|-------------|
| Pyannote | Yes (HF Token) | 95%+ | Fast | Yes |
| Simple-Diarizer | No | 85-90% | Medium | Partial |
| None | No | N/A | N/A | N/A |

## Troubleshooting

### "HF_TOKEN not set" Message
This is informational - the pipeline continues without speaker diarization.

### Simple-Diarizer Installation Issues
```bash
# If you encounter issues, try:
pip install --upgrade pip
pip install simple-diarizer
```

### Checking Active Backend
The pipeline logs which backend is being used:
```
[3/3] Running Speaker Diarization...
  Using backend: pyannote
```

## Future Enhancements

- NVIDIA NeMo integration (planned)
- Custom speaker embedding models
- Real-time diarization support

## Summary

The Hendrix pipeline now works seamlessly with or without speaker diarization. For best results, we recommend setting up Pyannote with a HuggingFace token, but the pipeline remains fully functional without it.