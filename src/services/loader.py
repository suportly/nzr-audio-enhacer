"""Audio file loading and validation service."""

from pathlib import Path

import numpy as np
import soundfile as sf

from src.models import (
    AudioFile,
    AudioFileNotFoundError,
    FileCorruptedError,
    InvalidFormatError,
    UnsupportedChannelsError,
)


def validate_wav_format(path: str | Path) -> bool:
    """Validate that a file is a valid WAV format.

    Args:
        path: Path to the audio file.

    Returns:
        True if the file is a valid WAV file.

    Raises:
        AudioFileNotFoundError: If the file doesn't exist.
        InvalidFormatError: If the file is not a valid WAV file.
    """
    path = Path(path)

    if not path.exists():
        raise AudioFileNotFoundError(str(path))

    # Check file extension
    if path.suffix.lower() != ".wav":
        raise InvalidFormatError(str(path), f"expected .wav extension, got {path.suffix}")

    # Try to read file info to validate format
    try:
        info = sf.info(str(path))
        if info.format != "WAV":
            raise InvalidFormatError(str(path), f"file format is {info.format}, not WAV")
        return True
    except sf.SoundFileError as e:
        raise InvalidFormatError(str(path), str(e))


def load_audio(path: str | Path) -> AudioFile:
    """Load an audio file and return an AudioFile instance.

    Args:
        path: Path to the audio file.

    Returns:
        AudioFile instance with loaded audio data.

    Raises:
        AudioFileNotFoundError: If the file doesn't exist.
        InvalidFormatError: If the file is not a valid WAV file.
        FileCorruptedError: If the file cannot be read.
        UnsupportedChannelsError: If the audio has more than 2 channels.
    """
    path = Path(path)

    # Validate format first
    validate_wav_format(path)

    try:
        # Load audio data
        samples, sample_rate = sf.read(str(path), dtype="float32")

        # Get file info for bit depth
        info = sf.info(str(path))

        # Determine bit depth from subtype
        bit_depth = _get_bit_depth(info.subtype)

        # Check channel count
        if samples.ndim == 1:
            channels = 1
        else:
            channels = samples.shape[1]
            if channels > 2:
                raise UnsupportedChannelsError(channels)

        return AudioFile.from_file(
            path=path,
            samples=samples,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
        )

    except sf.SoundFileError as e:
        raise FileCorruptedError(str(path), str(e))
    except MemoryError:
        raise FileCorruptedError(str(path), "file too large to load into memory")


def _get_bit_depth(subtype: str) -> int:
    """Extract bit depth from soundfile subtype string.

    Args:
        subtype: Soundfile subtype string (e.g., "PCM_16", "PCM_24").

    Returns:
        Bit depth as integer.
    """
    subtype_to_bits = {
        "PCM_S8": 8,
        "PCM_U8": 8,
        "PCM_16": 16,
        "PCM_24": 24,
        "PCM_32": 32,
        "FLOAT": 32,
        "DOUBLE": 64,
    }
    return subtype_to_bits.get(subtype, 16)
