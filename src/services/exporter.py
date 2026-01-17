"""Audio file exporting service."""

import os
from pathlib import Path

import numpy as np
import soundfile as sf

from src.models import AudioFile, InsufficientSpaceError, OutputWriteError


def generate_output_path(input_path: str | Path, suffix: str = "_enhanced") -> Path:
    """Generate an output file path based on the input path.

    Args:
        input_path: Path to the input file.
        suffix: Suffix to append before the extension.

    Returns:
        Path object for the output file.

    Example:
        >>> generate_output_path("/path/to/song.wav")
        PosixPath('/path/to/song_enhanced.wav')
    """
    input_path = Path(input_path)
    stem = input_path.stem
    extension = input_path.suffix
    parent = input_path.parent

    return parent / f"{stem}{suffix}{extension}"


def save_audio(
    audio_file: AudioFile,
    output_path: str | Path,
    bit_depth: int | None = None,
) -> bool:
    """Save an AudioFile to disk.

    Args:
        audio_file: AudioFile instance to save.
        output_path: Destination path for the output file.
        bit_depth: Output bit depth (defaults to input bit depth or 24).

    Returns:
        True if save was successful.

    Raises:
        InsufficientSpaceError: If there's not enough disk space.
        OutputWriteError: If the file cannot be written.
    """
    output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine output bit depth
    if bit_depth is None:
        # Default to 24-bit for better quality, or match input
        bit_depth = max(audio_file.bit_depth, 24)

    # Map bit depth to soundfile subtype
    subtype = _get_subtype(bit_depth)

    # Check available disk space (rough estimate)
    estimated_size = _estimate_file_size(audio_file, bit_depth)
    if not _has_sufficient_space(output_path.parent, estimated_size):
        raise InsufficientSpaceError(str(output_path))

    try:
        # Ensure samples are in the right range for integer formats
        samples = audio_file.samples
        if subtype.startswith("PCM_"):
            # Clip to valid range for PCM formats
            samples = np.clip(samples, -1.0, 1.0)

        sf.write(
            str(output_path),
            samples,
            audio_file.sample_rate,
            subtype=subtype,
            format="WAV",
        )
        return True

    except sf.SoundFileError as e:
        raise OutputWriteError(str(output_path), str(e))
    except PermissionError:
        raise OutputWriteError(str(output_path), "permission denied")
    except OSError as e:
        raise OutputWriteError(str(output_path), str(e))


def _get_subtype(bit_depth: int) -> str:
    """Get soundfile subtype for a given bit depth.

    Args:
        bit_depth: Desired bit depth.

    Returns:
        Soundfile subtype string.
    """
    bit_depth_to_subtype = {
        8: "PCM_U8",
        16: "PCM_16",
        24: "PCM_24",
        32: "FLOAT",
    }
    return bit_depth_to_subtype.get(bit_depth, "PCM_24")


def _estimate_file_size(audio_file: AudioFile, bit_depth: int) -> int:
    """Estimate the output file size in bytes.

    Args:
        audio_file: AudioFile to be saved.
        bit_depth: Output bit depth.

    Returns:
        Estimated file size in bytes.
    """
    bytes_per_sample = bit_depth // 8
    num_samples = audio_file.num_samples
    channels = audio_file.channels

    # WAV header is typically 44 bytes, add some margin
    header_size = 100
    data_size = num_samples * channels * bytes_per_sample

    return header_size + data_size


def _has_sufficient_space(directory: Path, required_bytes: int) -> bool:
    """Check if directory has sufficient disk space.

    Args:
        directory: Directory to check.
        required_bytes: Required space in bytes.

    Returns:
        True if sufficient space is available.
    """
    try:
        stat = os.statvfs(str(directory))
        available = stat.f_bavail * stat.f_frsize
        # Add 10% margin
        return available > required_bytes * 1.1
    except (OSError, AttributeError):
        # If we can't check, assume there's space
        return True
