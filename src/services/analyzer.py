"""Audio quality analysis service."""

import numpy as np
import librosa

from src.models import AudioFile, QualityMetrics


def analyze_quality(audio_file: AudioFile) -> QualityMetrics:
    """Analyze audio quality and return metrics.

    Args:
        audio_file: AudioFile instance to analyze.

    Returns:
        QualityMetrics with assessment of audio quality.
    """
    samples = audio_file.samples
    sr = audio_file.sample_rate

    # Ensure mono for analysis (average channels if stereo)
    if samples.ndim > 1:
        samples_mono = np.mean(samples, axis=1)
    else:
        samples_mono = samples

    # Calculate individual metrics
    snr_db = estimate_snr(samples_mono, sr)
    spectral_flatness = calculate_spectral_flatness(samples_mono, sr)
    dynamic_range_db = calculate_dynamic_range(samples_mono)
    clipping_ratio = calculate_clipping_ratio(samples_mono)
    silence_ratio = calculate_silence_ratio(samples_mono)

    # Calculate overall quality score (0.0 to 1.0)
    quality_score = _calculate_quality_score(
        snr_db=snr_db,
        spectral_flatness=spectral_flatness,
        dynamic_range_db=dynamic_range_db,
        clipping_ratio=clipping_ratio,
        silence_ratio=silence_ratio,
    )

    return QualityMetrics(
        snr_db=snr_db,
        spectral_flatness=spectral_flatness,
        dynamic_range_db=dynamic_range_db,
        clipping_ratio=clipping_ratio,
        silence_ratio=silence_ratio,
        quality_score=quality_score,
    )


def estimate_snr(samples: np.ndarray, sr: int) -> float:
    """Estimate signal-to-noise ratio in decibels.

    Uses a simple approach: compare RMS of the loudest sections
    to the quietest sections.

    Args:
        samples: Audio samples (mono).
        sr: Sample rate.

    Returns:
        Estimated SNR in decibels.
    """
    # Frame the audio into chunks
    frame_length = int(sr * 0.05)  # 50ms frames
    hop_length = frame_length // 2

    # Calculate RMS for each frame
    frames = librosa.util.frame(samples, frame_length=frame_length, hop_length=hop_length)
    rms_per_frame = np.sqrt(np.mean(frames**2, axis=0))

    # Avoid log of zero
    rms_per_frame = np.maximum(rms_per_frame, 1e-10)

    # Signal: top 10% loudest frames
    # Noise: bottom 10% quietest non-silent frames
    sorted_rms = np.sort(rms_per_frame)

    # Find non-silent frames (above -60 dB threshold)
    non_silent_mask = rms_per_frame > 1e-3
    if np.sum(non_silent_mask) < 10:
        # Very quiet or silent audio
        return 0.0

    non_silent_rms = sorted_rms[sorted_rms > 1e-3]

    n_frames = len(non_silent_rms)
    top_10_percent = max(1, n_frames // 10)
    bottom_10_percent = max(1, n_frames // 10)

    signal_rms = np.mean(non_silent_rms[-top_10_percent:])
    noise_rms = np.mean(non_silent_rms[:bottom_10_percent])

    if noise_rms < 1e-10:
        return 60.0  # Very clean signal

    snr = 20 * np.log10(signal_rms / noise_rms)
    return float(np.clip(snr, 0, 60))


def calculate_spectral_flatness(samples: np.ndarray, sr: int) -> float:
    """Calculate spectral flatness (0 = tonal, 1 = noise-like).

    Args:
        samples: Audio samples (mono).
        sr: Sample rate.

    Returns:
        Average spectral flatness (0.0 to 1.0).
    """
    # Calculate spectral flatness using librosa
    flatness = librosa.feature.spectral_flatness(y=samples, n_fft=2048, hop_length=512)

    # Average across all frames
    return float(np.mean(flatness))


def calculate_dynamic_range(samples: np.ndarray) -> float:
    """Calculate dynamic range (peak to RMS difference) in decibels.

    Args:
        samples: Audio samples (mono).

    Returns:
        Dynamic range in decibels.
    """
    peak = np.max(np.abs(samples))
    rms = np.sqrt(np.mean(samples**2))

    if rms < 1e-10 or peak < 1e-10:
        return 0.0

    # Dynamic range = peak level - RMS level (in dB)
    peak_db = 20 * np.log10(peak)
    rms_db = 20 * np.log10(rms)

    return float(peak_db - rms_db)


def calculate_clipping_ratio(samples: np.ndarray, threshold: float = 0.99) -> float:
    """Calculate the ratio of samples that appear to be clipped.

    Args:
        samples: Audio samples (mono).
        threshold: Amplitude threshold for detecting clipping.

    Returns:
        Ratio of clipped samples (0.0 to 1.0).
    """
    if len(samples) == 0:
        return 0.0

    clipped_count = np.sum(np.abs(samples) >= threshold)
    return float(clipped_count / len(samples))


def calculate_silence_ratio(samples: np.ndarray, threshold_db: float = -60) -> float:
    """Calculate the ratio of silent sections in the audio.

    Args:
        samples: Audio samples (mono).
        threshold_db: Silence threshold in decibels.

    Returns:
        Ratio of silent samples (0.0 to 1.0).
    """
    if len(samples) == 0:
        return 1.0

    # Convert threshold to linear
    threshold_linear = 10 ** (threshold_db / 20)

    silent_count = np.sum(np.abs(samples) < threshold_linear)
    return float(silent_count / len(samples))


def _calculate_quality_score(
    snr_db: float,
    spectral_flatness: float,
    dynamic_range_db: float,
    clipping_ratio: float,
    silence_ratio: float,
) -> float:
    """Calculate overall quality score from individual metrics.

    Args:
        snr_db: Signal-to-noise ratio in dB.
        spectral_flatness: Spectral flatness (0 to 1).
        dynamic_range_db: Dynamic range in dB.
        clipping_ratio: Ratio of clipped samples.
        silence_ratio: Ratio of silent samples.

    Returns:
        Quality score from 0.0 (poor) to 1.0 (excellent).
    """
    # SNR score: 0 dB -> 0, 40+ dB -> 1
    snr_score = np.clip(snr_db / 40, 0, 1)

    # Spectral flatness penalty: higher flatness (more noise) is worse
    # Typical music has flatness around 0.1-0.3
    flatness_score = 1 - np.clip(spectral_flatness / 0.5, 0, 1)

    # Dynamic range score: 6-20 dB is typical for mastered music
    # Too little (<6) or too much (>30) can indicate problems
    if dynamic_range_db < 6:
        dr_score = dynamic_range_db / 6
    elif dynamic_range_db <= 20:
        dr_score = 1.0
    else:
        dr_score = max(0, 1 - (dynamic_range_db - 20) / 20)

    # Clipping penalty: any clipping reduces quality
    clipping_score = 1 - np.clip(clipping_ratio * 100, 0, 1)  # 1% clipping -> 0 score

    # Silence is okay, but too much silence (>90%) is suspicious
    silence_score = 1 if silence_ratio < 0.9 else 0.5

    # Weighted combination
    weights = {
        "snr": 0.35,
        "flatness": 0.20,
        "dynamic_range": 0.20,
        "clipping": 0.20,
        "silence": 0.05,
    }

    score = (
        weights["snr"] * snr_score
        + weights["flatness"] * flatness_score
        + weights["dynamic_range"] * dr_score
        + weights["clipping"] * clipping_score
        + weights["silence"] * silence_score
    )

    return float(np.clip(score, 0, 1))
