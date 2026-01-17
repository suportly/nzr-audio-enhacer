"""Noise reduction service using spectral gating and AI."""

import numpy as np
import noisereduce as nr

from src.models import AudioFile, ModelUnavailableError

# AI imports - optional
try:
    from df.enhance import enhance as df_enhance
    from src.services.ai_models import is_model_available, load_deepfilternet
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


def reduce_noise_spectral(
    audio_file: AudioFile,
    strength: float = 0.5,
    stationary: bool = False,
) -> np.ndarray:
    """Apply spectral gating noise reduction.

    Uses the noisereduce library to perform spectral gating based
    noise reduction. Works well for stationary noise like hum, hiss,
    and constant background noise.

    Args:
        audio_file: AudioFile instance to process.
        strength: Noise reduction intensity (0.0 to 1.0).
                  Higher values = more aggressive noise reduction.
        stationary: If True, use stationary noise reduction (better for
                    constant noise). If False, use non-stationary
                    (better for varying noise).

    Returns:
        Processed audio samples as numpy array.
    """
    samples = audio_file.samples
    sr = audio_file.sample_rate

    # Scale strength to noisereduce parameters
    # prop_decrease controls how much noise is reduced
    prop_decrease = 0.5 + (strength * 0.5)  # Range: 0.5 to 1.0

    # n_std_thresh controls sensitivity to noise
    # Lower = more aggressive, Higher = more conservative
    n_std_thresh = 2.0 - (strength * 1.0)  # Range: 1.0 to 2.0

    if samples.ndim == 1:
        # Mono audio
        reduced = nr.reduce_noise(
            y=samples,
            sr=sr,
            stationary=stationary,
            prop_decrease=prop_decrease,
            n_std_thresh_stationary=n_std_thresh,
        )
    else:
        # Stereo audio - process each channel
        reduced = np.zeros_like(samples)
        for ch in range(samples.shape[1]):
            reduced[:, ch] = nr.reduce_noise(
                y=samples[:, ch],
                sr=sr,
                stationary=stationary,
                prop_decrease=prop_decrease,
                n_std_thresh_stationary=n_std_thresh,
            )

    return reduced


def reduce_noise_ai(audio_file: AudioFile) -> np.ndarray:
    """Apply AI-based noise reduction using DeepFilterNet.

    Uses a neural network model for superior noise reduction,
    especially effective for heavily degraded audio.

    Args:
        audio_file: AudioFile instance to process.

    Returns:
        Processed audio samples as numpy array.

    Raises:
        ModelUnavailableError: If DeepFilterNet is not available.
    """
    if not AI_AVAILABLE:
        raise ModelUnavailableError("DeepFilterNet")

    if not is_model_available():
        raise ModelUnavailableError("DeepFilterNet")

    try:
        model, df_state, target_sr = load_deepfilternet()

        samples = audio_file.samples
        sr = audio_file.sample_rate

        # DeepFilterNet expects specific sample rate (typically 48kHz)
        # Resample if necessary
        if sr != target_sr:
            import librosa
            if samples.ndim == 1:
                samples_resampled = librosa.resample(samples, orig_sr=sr, target_sr=target_sr)
            else:
                # Resample each channel
                samples_resampled = np.zeros(
                    (int(len(samples) * target_sr / sr), samples.shape[1]),
                    dtype=samples.dtype
                )
                for ch in range(samples.shape[1]):
                    samples_resampled[:, ch] = librosa.resample(
                        samples[:, ch], orig_sr=sr, target_sr=target_sr
                    )
        else:
            samples_resampled = samples

        # DeepFilterNet processes mono or converts internally
        # Pass the audio through the enhancement
        enhanced = df_enhance(model, df_state, samples_resampled)

        # Resample back to original sample rate if needed
        if sr != target_sr:
            import librosa
            if enhanced.ndim == 1:
                enhanced = librosa.resample(enhanced, orig_sr=target_sr, target_sr=sr)
            else:
                enhanced_original_sr = np.zeros_like(samples)
                for ch in range(enhanced.shape[1]):
                    enhanced_original_sr[:, ch] = librosa.resample(
                        enhanced[:, ch], orig_sr=target_sr, target_sr=sr
                    )
                enhanced = enhanced_original_sr

        return enhanced

    except Exception as e:
        raise ModelUnavailableError(f"DeepFilterNet - {e}")


def reduce_noise_with_fallback(
    audio_file: AudioFile,
    strength: float = 0.5,
    use_ai: bool = True,
) -> tuple[np.ndarray, str]:
    """Apply noise reduction with AI fallback to spectral gating.

    Attempts AI enhancement first if requested and available,
    falls back to spectral gating if AI fails.

    Args:
        audio_file: AudioFile instance to process.
        strength: Noise reduction intensity for spectral gating.
        use_ai: Whether to attempt AI enhancement.

    Returns:
        Tuple of (processed samples, method used).
    """
    if use_ai and AI_AVAILABLE:
        try:
            if is_model_available():
                samples = reduce_noise_ai(audio_file)
                return samples, "deepfilternet"
        except ModelUnavailableError:
            pass  # Fall through to spectral gating
        except Exception:
            pass  # Fall through to spectral gating

    # Fallback to spectral gating
    samples = reduce_noise_spectral(audio_file, strength)
    return samples, "spectral_gating"


def reduce_noise_adaptive(
    audio_file: AudioFile,
    strength: float = 0.5,
) -> np.ndarray:
    """Apply adaptive (non-stationary) noise reduction.

    Better for audio with varying background noise like
    recordings in different environments.

    Args:
        audio_file: AudioFile instance to process.
        strength: Noise reduction intensity (0.0 to 1.0).

    Returns:
        Processed audio samples as numpy array.
    """
    return reduce_noise_spectral(audio_file, strength, stationary=False)


def reduce_noise_stationary(
    audio_file: AudioFile,
    strength: float = 0.5,
) -> np.ndarray:
    """Apply stationary noise reduction.

    Better for audio with constant background noise like
    hum, hiss, or fan noise.

    Args:
        audio_file: AudioFile instance to process.
        strength: Noise reduction intensity (0.0 to 1.0).

    Returns:
        Processed audio samples as numpy array.
    """
    return reduce_noise_spectral(audio_file, strength, stationary=True)
