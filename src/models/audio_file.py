"""AudioFile data class for representing audio files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class AudioFile:
    """Represents an input or output audio file.

    Attributes:
        path: Absolute file path to the audio file.
        format: Audio format identifier (e.g., "wav").
        sample_rate: Samples per second (Hz).
        bit_depth: Bits per sample (8, 16, 24, or 32).
        channels: Number of audio channels (1 for mono, 2 for stereo).
        duration: Length in seconds.
        samples: Raw audio data as numpy array.
    """

    path: Path
    format: str
    sample_rate: int
    bit_depth: int
    channels: int
    duration: float
    samples: np.ndarray = field(repr=False)

    @property
    def is_mono(self) -> bool:
        """Check if audio is mono."""
        return self.channels == 1

    @property
    def is_stereo(self) -> bool:
        """Check if audio is stereo."""
        return self.channels == 2

    @property
    def num_samples(self) -> int:
        """Total number of samples in the audio."""
        return self.samples.shape[0]

    @classmethod
    def from_file(
        cls,
        path: Path,
        samples: np.ndarray,
        sample_rate: int,
        bit_depth: int = 16,
    ) -> "AudioFile":
        """Create an AudioFile from loaded audio data.

        Args:
            path: Path to the audio file.
            samples: Audio samples as numpy array.
            sample_rate: Sample rate in Hz.
            bit_depth: Bits per sample.

        Returns:
            AudioFile instance.
        """
        if samples.ndim == 1:
            channels = 1
        else:
            channels = samples.shape[1]

        duration = len(samples) / sample_rate

        return cls(
            path=Path(path),
            format=Path(path).suffix.lstrip(".").lower(),
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            channels=channels,
            duration=duration,
            samples=samples,
        )
