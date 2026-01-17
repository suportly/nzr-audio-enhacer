"""Dynamic range processing service."""

import numpy as np

from src.models import EnhancementConfig


def compress_dynamics(
    samples: np.ndarray,
    config: EnhancementConfig,
) -> np.ndarray:
    """Apply dynamic range compression to audio.

    Uses a soft-knee compressor to gently control dynamics
    without over-processing.

    Args:
        samples: Audio samples (mono or stereo).
        config: Enhancement configuration.

    Returns:
        Compressed audio samples.
    """
    if not config.dynamics_enabled:
        return samples

    # Compression parameters based on config
    if config.preserve_dynamics:
        # Gentle compression for preserving dynamics
        threshold_db = -18.0
        ratio = 2.0  # 2:1 ratio
        attack_ms = 10.0
        release_ms = 100.0
        knee_db = 6.0
    else:
        # More aggressive compression
        threshold_db = -24.0
        ratio = 4.0  # 4:1 ratio
        attack_ms = 5.0
        release_ms = 50.0
        knee_db = 3.0

    return _apply_compression(
        samples,
        threshold_db=threshold_db,
        ratio=ratio,
        attack_ms=attack_ms,
        release_ms=release_ms,
        knee_db=knee_db,
        makeup_gain_db=0.0,  # We'll normalize separately
    )


def normalize_loudness(
    samples: np.ndarray,
    target_lufs: float = -14.0,
    sr: int = 44100,
) -> np.ndarray:
    """Normalize audio to a target loudness in LUFS.

    Uses a simplified loudness measurement for normalization.
    For broadcast-standard LUFS, a proper ITU-R BS.1770 implementation
    would be needed.

    Args:
        samples: Audio samples (mono or stereo).
        target_lufs: Target loudness in LUFS.
        sr: Sample rate.

    Returns:
        Normalized audio samples.
    """
    # Calculate current loudness (simplified RMS-based approach)
    current_lufs = _estimate_loudness_lufs(samples)

    if current_lufs is None or np.isinf(current_lufs):
        return samples

    # Calculate required gain
    gain_db = target_lufs - current_lufs

    # Limit gain to prevent clipping and excessive boost
    gain_db = np.clip(gain_db, -20.0, 20.0)

    # Apply gain
    gain_linear = 10 ** (gain_db / 20)
    normalized = samples * gain_linear

    # Apply soft limiter to prevent clipping
    normalized = _soft_clip(normalized, threshold=0.95)

    return normalized


def _apply_compression(
    samples: np.ndarray,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    knee_db: float,
    makeup_gain_db: float,
    sr: int = 44100,
) -> np.ndarray:
    """Apply dynamic range compression.

    Args:
        samples: Audio samples.
        threshold_db: Compression threshold in dB.
        ratio: Compression ratio (e.g., 4 for 4:1).
        attack_ms: Attack time in milliseconds.
        release_ms: Release time in milliseconds.
        knee_db: Soft knee width in dB.
        makeup_gain_db: Post-compression gain in dB.
        sr: Sample rate.

    Returns:
        Compressed audio samples.
    """
    # Convert parameters
    threshold_linear = 10 ** (threshold_db / 20)
    attack_samples = int(sr * attack_ms / 1000)
    release_samples = int(sr * release_ms / 1000)

    # Work with absolute values for envelope
    if samples.ndim == 1:
        envelope = np.abs(samples)
    else:
        # Use max of channels for stereo
        envelope = np.max(np.abs(samples), axis=1)

    # Smooth envelope with attack/release
    smoothed_env = _smooth_envelope(envelope, attack_samples, release_samples)

    # Calculate gain reduction
    gain_reduction = _calculate_gain_reduction(
        smoothed_env, threshold_linear, ratio, knee_db
    )

    # Apply gain reduction
    if samples.ndim == 1:
        compressed = samples * gain_reduction
    else:
        compressed = samples * gain_reduction[:, np.newaxis]

    # Apply makeup gain
    if makeup_gain_db != 0:
        makeup_linear = 10 ** (makeup_gain_db / 20)
        compressed *= makeup_linear

    return compressed


def _smooth_envelope(
    envelope: np.ndarray,
    attack_samples: int,
    release_samples: int,
) -> np.ndarray:
    """Smooth an envelope with attack and release times.

    Args:
        envelope: Input envelope.
        attack_samples: Attack time in samples.
        release_samples: Release time in samples.

    Returns:
        Smoothed envelope.
    """
    smoothed = np.zeros_like(envelope)
    smoothed[0] = envelope[0]

    attack_coef = np.exp(-1.0 / max(attack_samples, 1))
    release_coef = np.exp(-1.0 / max(release_samples, 1))

    for i in range(1, len(envelope)):
        if envelope[i] > smoothed[i - 1]:
            # Attack phase
            coef = attack_coef
        else:
            # Release phase
            coef = release_coef

        smoothed[i] = coef * smoothed[i - 1] + (1 - coef) * envelope[i]

    return smoothed


def _calculate_gain_reduction(
    envelope: np.ndarray,
    threshold: float,
    ratio: float,
    knee_db: float,
) -> np.ndarray:
    """Calculate gain reduction based on envelope and compressor settings.

    Args:
        envelope: Smoothed envelope.
        threshold: Threshold in linear scale.
        ratio: Compression ratio.
        knee_db: Soft knee width in dB.

    Returns:
        Gain reduction array (multiply with signal).
    """
    gain = np.ones_like(envelope)

    # Avoid log of zero
    envelope_safe = np.maximum(envelope, 1e-10)
    envelope_db = 20 * np.log10(envelope_safe)
    threshold_db = 20 * np.log10(max(threshold, 1e-10))

    # Calculate gain reduction for each sample
    for i in range(len(envelope)):
        level_db = envelope_db[i]

        if level_db <= threshold_db - knee_db / 2:
            # Below knee - no compression
            output_db = level_db
        elif level_db >= threshold_db + knee_db / 2:
            # Above knee - full compression
            output_db = threshold_db + (level_db - threshold_db) / ratio
        else:
            # In the knee - soft transition
            knee_factor = (level_db - threshold_db + knee_db / 2) / knee_db
            compression_amount = knee_factor * knee_factor * (1 / ratio - 1) / 2
            output_db = level_db + compression_amount * (level_db - threshold_db + knee_db / 2)

        gain_reduction_db = output_db - level_db
        gain[i] = 10 ** (gain_reduction_db / 20)

    return gain


def _estimate_loudness_lufs(samples: np.ndarray) -> float | None:
    """Estimate loudness in LUFS (simplified).

    This is a simplified RMS-based estimation, not a full
    ITU-R BS.1770 implementation.

    Args:
        samples: Audio samples.

    Returns:
        Estimated loudness in LUFS, or None if silent.
    """
    if samples.ndim > 1:
        # Sum channels for loudness
        mono = np.mean(samples, axis=1)
    else:
        mono = samples

    rms = np.sqrt(np.mean(mono**2))

    if rms < 1e-10:
        return None

    # Simplified conversion from RMS to LUFS
    # This is an approximation; true LUFS requires K-weighting
    lufs = 20 * np.log10(rms) - 0.691

    return float(lufs)


def _soft_clip(samples: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Apply soft clipping to prevent hard clipping.

    Args:
        samples: Audio samples.
        threshold: Threshold above which soft clipping begins.

    Returns:
        Soft-clipped samples.
    """
    # Use tanh-based soft clipping
    clipped = np.where(
        np.abs(samples) <= threshold,
        samples,
        np.sign(samples) * (threshold + (1 - threshold) * np.tanh(
            (np.abs(samples) - threshold) / (1 - threshold)
        ))
    )
    return clipped
