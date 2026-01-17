"""Data models for the music enhancer."""

from .audio_file import AudioFile
from .config import EnhancementConfig, QualityLevel
from .errors import (
    AudioFileNotFoundError,
    EnhancerError,
    FileCorruptedError,
    InsufficientSpaceError,
    InvalidFormatError,
    ModelUnavailableError,
    OutputWriteError,
    ProcessingFailedError,
    UnsupportedChannelsError,
)
from .metrics import QualityMetrics
from .result import ProcessingResult
from .stage import ProcessingStage

__all__ = [
    # Data classes
    "AudioFile",
    "EnhancementConfig",
    "ProcessingResult",
    "ProcessingStage",
    "QualityMetrics",
    "QualityLevel",
    # Errors
    "EnhancerError",
    "AudioFileNotFoundError",
    "FileCorruptedError",
    "InsufficientSpaceError",
    "InvalidFormatError",
    "ModelUnavailableError",
    "OutputWriteError",
    "ProcessingFailedError",
    "UnsupportedChannelsError",
]
