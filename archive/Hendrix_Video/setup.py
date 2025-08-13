"""Setup script for Hendrix Video Analysis Pipeline."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "ipython>=8.0.0",
    "jupyter>=1.0.0",
]

setup(
    name="hendrix-video-analysis",
    version="0.1.0",
    author="Hendrix Video Analysis Contributors",
    author_email="",
    description="A sophisticated video analysis pipeline using state-of-the-art computer vision and language models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Hendrix_Video_Analysis",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/Hendrix_Video_Analysis/issues",
        "Documentation": "https://github.com/yourusername/Hendrix_Video_Analysis/tree/main/docs",
        "Source Code": "https://github.com/yourusername/Hendrix_Video_Analysis",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "gpu": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "torchaudio>=2.0.0",
        ],
        "all": requirements + dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "hendrix-analyze=main:main",
            "hendrix-download-models=utils.download_models:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    zip_safe=False,
    keywords=[
        "video analysis",
        "computer vision",
        "shot detection",
        "scene understanding",
        "llava",
        "transnetv2",
        "video processing",
        "ai",
        "machine learning",
    ],
)