# Hendrix Video Analysis - Setup Guide

## Quick Start

1. **Initialize the project** (run this first):
   ```bash
   python3 init_project.py
   ```

2. **Set up the environment**:
   ```bash
   source setup_env.sh
   ```

3. **Run the pipeline**:
   ```bash
   python src/main.py path/to/video.mp4
   ```

## Directory Structure

After initialization, the project will have the following structure:

```
Hendrix_Video_Analysis/
├── cache/                    # Model cache directories
│   ├── huggingface/         # HuggingFace models
│   ├── transformers/        # Transformers cache
│   ├── torch/               # PyTorch models
│   └── datasets/            # Datasets cache
├── output/                  # Analysis results
├── temp/                    # Temporary files
├── keyframes/               # Extracted keyframes
├── src/                     # Source code
├── venv/                    # Virtual environment
└── config.yaml              # Configuration
```

## Path Configuration

All paths are now **relative to the project root**, making the project portable:

- Model caches: `./cache/`
- Output files: `./output/`
- Temporary files: `./temp/`
- Keyframes: `./keyframes/`

## Environment Variables

The following environment variables are automatically set by `setup_env.sh`:

- `HF_HOME`: HuggingFace cache directory
- `TRANSFORMERS_CACHE`: Transformers cache directory
- `TORCH_HOME`: PyTorch cache directory
- `HF_DATASETS_CACHE`: Datasets cache directory

## Moving the Project

To move the project to a different location:

1. Copy the entire project directory
2. Run `python3 init_project.py` in the new location
3. The script will update all paths automatically

## Troubleshooting

### Virtual Environment Issues
If the virtual environment has issues after moving:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Model Cache
Models will be downloaded to the `cache/` directory within the project.
This keeps all project files contained and makes cleanup easy.

### Permissions
Ensure the scripts are executable:
```bash
chmod +x setup_env.sh init_project.py
```