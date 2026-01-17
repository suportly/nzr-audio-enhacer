"""Pytest configuration and fixtures for audio testing."""

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path
import tempfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_rate():
    """Standard sample rate for test audio."""
    return 44100


@pytest.fixture
def mono_samples(sample_rate):
    """Generate mono test audio samples (3 seconds of sine wave with noise)."""
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    # 440 Hz sine wave
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)

    # Add some noise
    noise = 0.05 * np.random.randn(len(t)).astype(np.float32)

    return signal + noise


@pytest.fixture
def stereo_samples(mono_samples):
    """Generate stereo test audio samples."""
    # Create stereo by duplicating mono with slight variation
    left = mono_samples
    right = mono_samples * 0.95 + 0.01 * np.random.randn(len(mono_samples)).astype(np.float32)
    return np.column_stack([left, right])


@pytest.fixture
def noisy_samples(sample_rate):
    """Generate noisy test audio samples (low SNR)."""
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    # 440 Hz sine wave (weaker signal)
    signal = 0.3 * np.sin(2 * np.pi * 440 * t)

    # Add heavy noise
    noise = 0.2 * np.random.randn(len(t)).astype(np.float32)

    return signal + noise


@pytest.fixture
def clean_samples(sample_rate):
    """Generate clean test audio samples (high SNR)."""
    duration = 3.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    # 440 Hz sine wave (strong signal)
    signal = 0.7 * np.sin(2 * np.pi * 440 * t)

    # Very little noise
    noise = 0.005 * np.random.randn(len(t)).astype(np.float32)

    return signal + noise


@pytest.fixture
def mono_wav_file(temp_dir, mono_samples, sample_rate):
    """Create a temporary mono WAV file."""
    path = temp_dir / "test_mono.wav"
    sf.write(str(path), mono_samples, sample_rate)
    return path


@pytest.fixture
def stereo_wav_file(temp_dir, stereo_samples, sample_rate):
    """Create a temporary stereo WAV file."""
    path = temp_dir / "test_stereo.wav"
    sf.write(str(path), stereo_samples, sample_rate)
    return path


@pytest.fixture
def noisy_wav_file(temp_dir, noisy_samples, sample_rate):
    """Create a temporary noisy WAV file."""
    path = temp_dir / "test_noisy.wav"
    sf.write(str(path), noisy_samples, sample_rate)
    return path


@pytest.fixture
def clean_wav_file(temp_dir, clean_samples, sample_rate):
    """Create a temporary clean WAV file."""
    path = temp_dir / "test_clean.wav"
    sf.write(str(path), clean_samples, sample_rate)
    return path
