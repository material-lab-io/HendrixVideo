#!/usr/bin/env python3
"""Analyze requirements.txt files to find common dependencies and conflicts."""

import os
from collections import defaultdict, Counter
from pathlib import Path

# Requirements data from each file
requirements_data = {
    "Hendrix_Comprehensive_Captioning": {
        "pyyaml": ">=6.0",
        "requests": ">=2.31.0",
        "torch": ">=2.0.0",
        "torchvision": ">=0.15.0",
        "transformers": ">=4.36.0",
        "pillow": ">=10.0.0",
        "accelerate": ">=0.25.0",
        "pytest": ">=7.4.0",
        "black": ">=23.0.0",
        "flake8": ">=6.0.0",
        "python-dateutil": ">=2.8.2"
    },
    "Hendrix_Character_Dialogue_Analysis/audio_processing_branch": {
        "torch": ">=2.0.0",
        "torchaudio": ">=2.0.0",
        "torchvision": ">=0.15.0",
        "openai-whisper": ">=20230314",
        "pyannote.audio": ">=3.0.0",
        "librosa": ">=0.10.0",
        "soundfile": ">=0.12.0",
        "pydub": ">=0.25.0",
        "transformers": ">=4.35.0",
        "datasets": ">=2.14.0",
        "speechbrain": ">=0.5.0",
        "ultralytics": ">=8.0.0",
        "insightface": ">=0.7.3",
        "onnxruntime-gpu": ">=1.16.0",
        "deepface": ">=0.0.79",
        "opencv-python": ">=4.8.0",
        "opencv-contrib-python": ">=4.8.0",
        "easyocr": ">=1.7.0",
        "pillow": ">=10.0.0",
        "requests": ">=2.31.0",
        "numpy": ">=1.24.0",
        "pandas": ">=2.0.0",
        "scikit-learn": ">=1.3.0",
        "scipy": ">=1.11.0",
        "moviepy": ">=1.0.3",
        "ffmpeg-python": ">=0.2.0",
        "tqdm": ">=4.65.0",
        "python-dotenv": ">=1.0.0",
        "pyyaml": ">=6.0",
        "jsonschema": ">=4.19.0",
        "matplotlib": ">=3.7.0",
        "seaborn": ">=0.12.0",
        "pytest": ">=7.4.0",
        "pytest-asyncio": ">=0.21.0",
        "ipython": ">=8.14.0",
        "jupyter": ">=1.0.0"
    },
    "Hendrix_Character_Dialogue_Analysis/visual_processing_branch": {
        "ultralytics": ">=8.0.0",
        "opencv-python": ">=4.8.0",
        "opencv-contrib-python": ">=4.8.0",
        "insightface": ">=0.7.3",
        "onnxruntime-gpu": ">=1.16.0",
        "mxnet": ">=1.9.1",
        "deepface": ">=0.0.79",
        "scenedetect": ">=0.6.0",
        "av": ">=10.0.0",
        "pillow": ">=10.0.0",
        "albumentations": ">=1.3.0",
        "imageio": ">=2.31.0",
        "imageio-ffmpeg": ">=0.4.8",
        "scikit-learn": ">=1.3.0",
        "faiss-gpu": ">=1.7.2",
        "hdbscan": ">=0.8.33",
        "umap-learn": ">=0.5.4",
        "numpy": ">=1.24.0",
        "pandas": ">=2.0.0",
        "scipy": ">=1.11.0",
        "matplotlib": ">=3.7.0",
        "seaborn": ">=0.12.0",
        "plotly": ">=5.16.0",
        "decord": ">=0.6.0",
        "vidgear": ">=0.3.0",
        "timm": ">=0.9.0",
        "torchvision": ">=0.15.0",
        "tqdm": ">=4.65.0",
        "python-dotenv": ">=1.0.0",
        "pyyaml": ">=6.0",
        "click": ">=8.1.0"
    },
    "Hendrix_Video": {
        "opencv-python": ">=4.8.0",
        "numpy": ">=1.26.0",
        "pillow": ">=10.0.0",
        "torch": ">=2.0.0",
        "torchvision": ">=0.15.0",
        "transformers": ">=4.30.0",
        "moviepy": ">=1.0.3",
        "ffmpeg-python": ">=0.2.0",
        "scipy": ">=1.11.0",
        "scikit-learn": ">=1.3.0",
        "accelerate": ">=0.20.0",
        "sentencepiece": ">=0.1.99",
        "protobuf": ">=4.23.0",
        "pyyaml": ">=6.0",
        "tqdm": ">=4.65.0",
        "pandas": ">=2.0.0",
        "python-dotenv": ">=1.0.0",
        "transnetv2-pytorch": ">=1.0.1",
        "pytest": ">=7.4.0",
        "pytest-asyncio": ">=0.21.0",
        "black": ">=23.0.0",
        "flake8": ">=6.0.0"
    },
    "hendrix_venv": {
        "requests": ">=2.27.1",
        "numpy": ">=1.14.0",
        "pandas": ">=0.23.4",
        "gdown": ">=3.10.1",
        "tqdm": ">=4.30.0",
        "pillow": ">=5.2.0",
        "opencv-python": ">=4.5.5.64",
        "tensorflow": ">=1.9.0",
        "keras": ">=2.2.0",
        "flask": ">=1.1.2",
        "flask_cors": ">=4.0.1",
        "mtcnn": ">=0.1.0",
        "retina-face": ">=0.0.14",
        "fire": ">=0.4.0",
        "gunicorn": ">=20.1.0"
    }
}

def parse_version(version_str):
    """Extract version number from version string."""
    if version_str.startswith(">="):
        return version_str[2:]
    elif version_str.startswith("=="):
        return version_str[2:]
    elif version_str.startswith(">"):
        return version_str[1:]
    return version_str

def compare_versions(v1, v2):
    """Compare two version strings."""
    try:
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        return 0
    except:
        return None

# Analyze dependencies
all_deps = defaultdict(list)
dep_counts = Counter()

for component, deps in requirements_data.items():
    for dep, version in deps.items():
        all_deps[dep].append((component, version))
        dep_counts[dep] += 1

# Find common dependencies (in 3+ components)
print("## COMMON DEPENDENCIES (in 3+ components)")
print("=" * 80)
common_deps = {dep: versions for dep, versions in all_deps.items() if len(versions) >= 3}
for dep in sorted(common_deps.keys()):
    versions = all_deps[dep]
    print(f"\n{dep}:")
    for component, version in versions:
        print(f"  - {component}: {version}")

# Find version conflicts
print("\n\n## VERSION CONFLICTS")
print("=" * 80)
conflicts = []
for dep, versions in all_deps.items():
    if len(versions) > 1:
        unique_versions = set(v[1] for v in versions)
        if len(unique_versions) > 1:
            # Check if there are actual conflicts
            parsed_versions = [(v[0], parse_version(v[1])) for v in versions]
            max_version = None
            max_component = None
            
            for component, version in parsed_versions:
                if max_version is None:
                    max_version = version
                    max_component = component
                else:
                    cmp = compare_versions(version, max_version)
                    if cmp is not None and cmp > 0:
                        max_version = version
                        max_component = component
            
            print(f"\n{dep}:")
            for component, version in versions:
                parsed = parse_version(version)
                is_max = parsed == max_version
                print(f"  - {component}: {version} {'[HIGHEST]' if is_max else ''}")

# Component-specific dependencies
print("\n\n## COMPONENT-SPECIFIC DEPENDENCIES")
print("=" * 80)
for dep, versions in all_deps.items():
    if len(versions) == 1:
        component, version = versions[0]
        print(f"{dep} ({version}) - Only in {component}")

# Group by component type
print("\n\n## DEPENDENCIES BY CATEGORY")
print("=" * 80)

categories = {
    "Core ML": ["torch", "torchvision", "torchaudio", "tensorflow", "keras"],
    "Transformers/LLMs": ["transformers", "accelerate", "sentencepiece", "protobuf"],
    "Computer Vision": ["opencv-python", "opencv-contrib-python", "pillow", "ultralytics", "insightface", "deepface"],
    "Audio Processing": ["openai-whisper", "pyannote.audio", "librosa", "soundfile", "pydub", "speechbrain"],
    "Video Processing": ["moviepy", "ffmpeg-python", "scenedetect", "av", "decord", "vidgear", "transnetv2-pytorch"],
    "Data Science": ["numpy", "pandas", "scipy", "scikit-learn"],
    "Utilities": ["pyyaml", "requests", "tqdm", "python-dotenv", "jsonschema"],
    "Development": ["pytest", "pytest-asyncio", "black", "flake8", "ipython", "jupyter"],
    "Web Framework": ["flask", "flask_cors", "gunicorn"],
    "Specialized": ["easyocr", "faiss-gpu", "hdbscan", "umap-learn", "mtcnn", "retina-face"]
}

for category, deps in categories.items():
    print(f"\n{category}:")
    for dep in deps:
        if dep in all_deps:
            count = len(all_deps[dep])
            print(f"  - {dep} (used in {count} components)")

print("\n\n## RECOMMENDATIONS FOR MODULAR REQUIREMENTS")
print("=" * 80)
print("""
1. Create a base requirements file with common dependencies
2. Create component-specific requirements files that include the base
3. Resolve version conflicts by using the highest version
4. Consider creating optional requirement groups for specific features
""")