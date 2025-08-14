# Changelog

All notable changes to the Hendrix Video Analysis Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation suite (USAGE_GUIDE.md, DEVELOPMENT_GUIDE.md)
- GitHub issue and PR templates
- Pre-commit hooks for code quality
- Basic test infrastructure with pytest
- CI/CD pipeline with GitHub Actions
- Setup.py and pyproject.toml for package installation
- Security policy and funding information
- Dependabot configuration for automated updates

### Changed
- Reorganized pipeline scripts into scripts/pipeline/ directory
- Enhanced README with badges and better structure
- Improved CLAUDE.md with testing and architecture details
- Updated configuration examples

### Fixed
- Removed temporary test scripts
- Cleaned up directory structure

## [2.0.0] - 2024-01-15

### Added
- Initial public release of Hendrix v2.0
- Three-component architecture:
  - Video Analysis: Shot detection and scene construction
  - Character & Dialogue: Speech transcription and face detection
  - Captioning: AI-powered caption generation
- Support for multiple vision-language models (LLaVA, GPT-4V)
- Modular requirement system
- Configuration profiles (fast, balanced, quality, test)
- Multiple output formats (SRT, WebVTT, JSON, HTML)

### Changed
- Complete reorganization from three separate projects to unified pipeline
- Centralized configuration management
- Improved error handling and logging

### Fixed
- Memory management issues with large videos
- GPU detection and fallback mechanisms

## [1.0.0] - 2023-11-01

### Added
- Initial proof of concept
- Basic video analysis capabilities
- Simple transcription support

---

[Unreleased]: https://github.com/yourusername/hendrix_12aug/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/yourusername/hendrix_12aug/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/hendrix_12aug/releases/tag/v1.0.0