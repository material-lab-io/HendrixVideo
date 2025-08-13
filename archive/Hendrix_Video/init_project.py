#!/usr/bin/env python3
"""
Initialize Hendrix Video Analysis project with proper directory structure and paths.
This script ensures all necessary directories exist and paths are correctly configured.
"""

import os
import sys
import yaml
from pathlib import Path


def init_project():
    """Initialize project directories and verify configuration."""
    
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    
    print(f"Initializing Hendrix Video Analysis project at: {project_root}")
    
    # Create necessary directories
    directories = [
        "cache/huggingface",
        "cache/transformers", 
        "cache/torch",
        "cache/datasets",
        "output",
        "temp",
        "keyframes"
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # Update .env file with absolute paths based on project location
    env_file = project_root / ".env"
    env_content = f"""# Environment variables for model storage
HF_HOME={project_root}/cache/huggingface
TRANSFORMERS_CACHE={project_root}/cache/transformers
TORCH_HOME={project_root}/cache/torch
HF_DATASETS_CACHE={project_root}/cache/datasets
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    print(f"✓ Updated .env file with project-specific paths")
    
    # Verify config.yaml exists and has correct structure
    config_file = project_root / "config.yaml"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Verify paths are relative
        paths_to_check = [
            ('general', 'temp_directory'),
            ('pipeline', 'keyframes_directory'),
            ('output', 'shots_file'),
            ('output', 'scenes_file'),
            ('output', 'analysis_file'),
            ('output', 'combined_output')
        ]
        
        all_relative = True
        for section, key in paths_to_check:
            if section in config and key in config[section]:
                path = config[section][key]
                if os.path.isabs(path):
                    all_relative = False
                    print(f"⚠ Warning: {section}.{key} has absolute path: {path}")
        
        if all_relative:
            print("✓ All paths in config.yaml are relative")
    else:
        print("⚠ Warning: config.yaml not found")
    
    # Check virtual environment
    venv_path = project_root / "venv"
    if venv_path.exists():
        print("✓ Virtual environment exists")
    else:
        print("⚠ Virtual environment not found. Run the following commands:")
        print(f"  cd {project_root}")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
    
    print("\n✅ Project initialization complete!")
    print("\nTo use the project:")
    print(f"  cd {project_root}")
    print("  source setup_env.sh  # This will activate the environment and set paths")
    print("  python src/main.py <video_file>")


if __name__ == "__main__":
    init_project()