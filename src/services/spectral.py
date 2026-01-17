"""Spectral enhancement (EQ) service using scipy filters."""

import numpy as np
from scipy import signal

from src.models import EnhancementConfig


def apply_eq(
    samples: np.ndarray,
    sr: int,
    config: EnhancementConfig,
) -> np.ndarray:
    """Apply equalization to audio samples.

    Applies a gentle EQ curve designed to improve clarity and balance
    for typical music content.

    Args:
        samples: Audio samples (mono or stereo).
        sr: Sample rate in Hz.
        config: Enhancement configuration.

    Returns:
        EQ'd audio samples.
    """
    if not config.eq_enabled:
        return samples

    # Apply a subtle presence boost and low-end warmth
    # These are gentle, music-appropriate adjustments

    # High-pass filter to remove subsonic rumble (below 30 Hz)
    samples = _highpass_filter(samples, sr, cutoff=30)

    # Low-shelf boost for warmth (around 100 Hz, +2 dB)
    samples = _low_shelf_filter(samples, sr, cutoff=100, gain_db=2.0)

    # Presence boost (around 3 kHz, +2 dB)
    samples = _peak_filter(samples, sr, center=3000, q=1.0, gain_db=2.0)

    # Air/brightness (around 12 kHz, +1.5 dB)
    samples = _high_shelf_filter(samples, sr, cutoff=12000, gain_db=1.5)

    return samples


def enhance_clarity(samples: np.ndarray, sr: int) -> np.ndarray:
    """Enhance audio clarity without full EQ processing.

    Focuses on improving intelligibility and presence without
    dramatically changing the tonal balance.

    Args:
        samples: Audio samples (mono or stereo).
        sr: Sample rate in Hz.

    Returns:
        Enhanced audio samples.
    """
    # Gentle presence boost around 2-4 kHz
    samples = _peak_filter(samples, sr, center=3000, q=0.7, gain_db=1.5)

    # Reduce muddiness around 300-400 Hz
    samples = _peak_filter(samples, sr, center=350, q=0.8, gain_db=-1.0)

    return samples


def _highpass_filter(samples: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
    """Apply a high-pass filter.

    Args:
        samples: Audio samples.
        sr: Sample rate.
        cutoff: Cutoff frequency in Hz.

    Returns:
        Filtered samples.
    """
    nyquist = sr / 2
    if cutoff >= nyquist:
        return samples

    normalized_cutoff = cutoff / nyquist
    b, a = signal.butter(2, normalized_cutoff, btype="high")

    return _apply_filter(samples, b, a)


def _low_shelf_filter(
    samples: np.ndarray,
    sr: int,
    cutoff: float,
    gain_db: float,
) -> np.ndarray:
    """Apply a low-shelf filter.

    Args:
        samples: Audio samples.
        sr: Sample rate.
        cutoff: Shelf frequency in Hz.
        gain_db: Gain in decibels.

    Returns:
        Filtered samples.
    """
    nyquist = sr / 2
    if cutoff >= nyquist:
        return samples

    # Design low-shelf filter coefficients
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * cutoff / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt(2)  # S = 1 for gentle slope

    b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
    b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
    b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
    a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
    a2 = (A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1, a1 / a0, a2 / a0])

    return _apply_filter(samples, b, a)


def _high_shelf_filter(
    samples: np.ndarray,
    sr: int,
    cutoff: float,
    gain_db: float,
) -> np.ndarray:
    """Apply a high-shelf filter.

    Args:
        samples: Audio samples.
        sr: Sample rate.
        cutoff: Shelf frequency in Hz.
        gain_db: Gain in decibels.

    Returns:
        Filtered samples.
    """
    nyquist = sr / 2
    if cutoff >= nyquist:
        return samples

    # Design high-shelf filter coefficients
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * cutoff / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt(2)

    b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
    b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
    a2 = (A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1, a1 / a0, a2 / a0])

    return _apply_filter(samples, b, a)


def _peak_filter(
    samples: np.ndarray,
    sr: int,
    center: float,
    q: float,
    gain_db: float,
) -> np.ndarray:
    """Apply a peaking EQ filter.

    Args:
        samples: Audio samples.
        sr: Sample rate.
        center: Center frequency in Hz.
        q: Q factor (bandwidth control).
        gain_db: Gain in decibels.

    Returns:
        Filtered samples.
    """
    nyquist = sr / 2
    if center >= nyquist:
        return samples

    # Design peaking filter coefficients
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * center / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / (2 * q)

    b0 = 1 + alpha * A
    b1 = -2 * cos_w0
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_w0
    a2 = 1 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1, a1 / a0, a2 / a0])

    return _apply_filter(samples, b, a)


def _apply_filter(samples: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Apply a filter to samples, handling mono and stereo.

    Args:
        samples: Audio samples.
        b: Numerator coefficients.
        a: Denominator coefficients.

    Returns:
        Filtered samples.
    """
    if samples.ndim == 1:
        return signal.filtfilt(b, a, samples)
    else:
        filtered = np.zeros_like(samples)
        for ch in range(samples.shape[1]):
            filtered[:, ch] = signal.filtfilt(b, a, samples[:, ch])
        return filtered
