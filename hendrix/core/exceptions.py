"""Custom exceptions for the hendrix package."""


class HendrixError(Exception):
    """Base exception for all hendrix errors."""
    pass


class ConfigurationError(HendrixError):
    """Raised when there's an issue with configuration."""
    pass


class ModelError(HendrixError):
    """Raised when there's an issue with model loading or inference."""
    pass


class VideoProcessingError(HendrixError):
    """Raised when video processing fails."""
    pass


class AudioProcessingError(HendrixError):
    """Raised when audio processing fails."""
    pass


class CaptionGenerationError(HendrixError):
    """Raised when caption generation fails."""
    pass