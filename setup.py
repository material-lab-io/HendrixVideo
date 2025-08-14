"""
Setup script for Hendrix Video Analysis Pipeline
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read version from __init__.py
version = "2.1.0"  # Update this for each release

setup(
    name="hendrix-video-analysis",
    version=version,
    author="Hendrix Contributors",
    author_email="contact@hendrix-project.org",
    description="AI-powered video analysis pipeline with shot detection, transcription, and caption generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hendrix_12aug",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/hendrix_12aug/issues",
        "Documentation": "https://github.com/yourusername/hendrix_12aug/tree/main/docs",
        "Source Code": "https://github.com/yourusername/hendrix_12aug",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(exclude=["tests*", "docs*", "examples*", "archive*"]),
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies only - full list in requirements/
        "numpy>=1.24.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "video": ["opencv-python>=4.8.0", "moviepy>=1.0.3"],
        "audio": ["openai-whisper>=20230918", "pyannote.audio>=3.0.0"],
        "ml": ["torch>=2.0.0", "transformers>=4.35.0"],
        "dev": ["pytest>=7.4.0", "black>=23.7.0", "flake8>=6.1.0"],
        "all": [
            # This would include all dependencies
            # In practice, point to requirements files
        ],
    },
    entry_points={
        "console_scripts": [
            "hendrix=hendrix_pipeline:main",
            "hendrix-pipeline=hendrix_pipeline:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hendrix": [
            "configs/*.yaml",
            "configs/**/*.yaml",
        ],
    },
    zip_safe=False,
)