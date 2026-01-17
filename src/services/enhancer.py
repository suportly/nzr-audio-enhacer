"""Main enhancement pipeline orchestrator."""

import time
from pathlib import Path

import numpy as np

from src.models import (
    AudioFile,
    EnhancementConfig,
    ProcessingFailedError,
    ProcessingResult,
    ProcessingStage,
    QualityLevel,
    QualityMetrics,
)
from src.services.analyzer import analyze_quality
from src.services.dynamics import compress_dynamics, normalize_loudness
from src.services.exporter import generate_output_path, save_audio
from src.services.noise_reduction import reduce_noise_spectral, reduce_noise_with_fallback
from src.services.spectral import apply_eq


def enhance_audio(
    audio_file: AudioFile,
    config: EnhancementConfig,
    output_path: Path | str | None = None,
) -> ProcessingResult:
    """Enhance audio quality using the full processing pipeline.

    Pipeline stages:
    1. Analyze input quality
    2. Select/adjust configuration based on quality
    3. Apply noise reduction
    4. Apply spectral enhancement (EQ)
    5. Apply dynamic range processing
    6. Validate output quality
    7. Export enhanced audio

    Args:
        audio_file: Input AudioFile to process.
        config: Enhancement configuration.
        output_path: Optional output path. If None, generates automatically.

    Returns:
        ProcessingResult with outcome details.
    """
    start_time = time.time()
    stages: list[ProcessingStage] = []

    try:
        # Stage 1: Analyze input quality
        stage_start = time.time()
        input_metrics = analyze_quality(audio_file)
        stages.append(ProcessingStage.completed(
            name="analysis",
            method="librosa",
            duration=time.time() - stage_start,
            parameters={"quality_score": input_metrics.quality_score},
        ))

        # Stage 2: Adjust config based on quality (if auto)
        if config.quality_level == QualityLevel.AUTO:
            config = select_config(input_metrics, config)

        # Start with original samples
        samples = audio_file.samples.copy()
        sr = audio_file.sample_rate

        # Stage 3: Noise reduction
        if config.noise_reduction_strength > 0:
            stage_start = time.time()

            # Create temporary AudioFile with current samples
            temp_audio = AudioFile(
                path=audio_file.path,
                format=audio_file.format,
                sample_rate=sr,
                bit_depth=audio_file.bit_depth,
                channels=audio_file.channels,
                duration=audio_file.duration,
                samples=samples,
            )

            # Use AI if enabled and quality warrants it
            use_ai = (
                config.ai_enhancement_enabled
                and input_metrics.needs_ai_enhancement
            )

            samples, nr_method = reduce_noise_with_fallback(
                temp_audio,
                config.noise_reduction_strength,
                use_ai=use_ai,
            )

            stages.append(ProcessingStage.completed(
                name="noise_reduction",
                method=nr_method,
                duration=time.time() - stage_start,
                parameters={
                    "strength": config.noise_reduction_strength,
                    "ai_used": nr_method == "deepfilternet",
                },
            ))
        else:
            stages.append(ProcessingStage.skipped("noise_reduction"))

        # Stage 4: Spectral enhancement (EQ)
        if config.eq_enabled:
            stage_start = time.time()
            samples = apply_eq(samples, sr, config)
            stages.append(ProcessingStage.completed(
                name="spectral",
                method="scipy_filters",
                duration=time.time() - stage_start,
                parameters={"eq_enabled": True},
            ))
        else:
            stages.append(ProcessingStage.skipped("spectral"))

        # Stage 5: Dynamic range processing
        if config.dynamics_enabled:
            stage_start = time.time()

            # Create temporary AudioFile for dynamics processing
            temp_audio = AudioFile(
                path=audio_file.path,
                format=audio_file.format,
                sample_rate=sr,
                bit_depth=audio_file.bit_depth,
                channels=audio_file.channels,
                duration=len(samples) / sr,
                samples=samples,
            )

            samples = compress_dynamics(samples, config)
            samples = normalize_loudness(samples, config.target_loudness_lufs, sr)
            stages.append(ProcessingStage.completed(
                name="dynamics",
                method="compression_normalization",
                duration=time.time() - stage_start,
                parameters={
                    "preserve_dynamics": config.preserve_dynamics,
                    "target_lufs": config.target_loudness_lufs,
                },
            ))
        else:
            stages.append(ProcessingStage.skipped("dynamics"))

        # Create output AudioFile
        output_audio = AudioFile(
            path=audio_file.path,  # Will be updated after save
            format="wav",
            sample_rate=sr,
            bit_depth=max(audio_file.bit_depth, 24),  # Upgrade to 24-bit
            channels=audio_file.channels,
            duration=len(samples) / sr,
            samples=samples,
        )

        # Stage 6: Analyze output quality
        stage_start = time.time()
        output_metrics = analyze_quality(output_audio)
        stages.append(ProcessingStage.completed(
            name="validation",
            method="quality_check",
            duration=time.time() - stage_start,
            parameters={"quality_score": output_metrics.quality_score},
        ))

        # Stage 7: Export
        stage_start = time.time()
        if output_path is None:
            output_path = generate_output_path(audio_file.path)
        else:
            output_path = Path(output_path)

        save_audio(output_audio, output_path)

        # Update output audio with final path
        output_audio = AudioFile(
            path=output_path,
            format="wav",
            sample_rate=sr,
            bit_depth=output_audio.bit_depth,
            channels=output_audio.channels,
            duration=output_audio.duration,
            samples=samples,
        )

        stages.append(ProcessingStage.completed(
            name="export",
            method="soundfile",
            duration=time.time() - stage_start,
            parameters={"path": str(output_path)},
        ))

        total_duration = time.time() - start_time

        return ProcessingResult(
            success=True,
            input_file=audio_file,
            output_file=output_audio,
            input_metrics=input_metrics,
            output_metrics=output_metrics,
            processing_stages=stages,
            duration_seconds=total_duration,
        )

    except Exception as e:
        total_duration = time.time() - start_time
        return ProcessingResult(
            success=False,
            input_file=audio_file,
            input_metrics=input_metrics if 'input_metrics' in locals() else None,
            processing_stages=stages,
            duration_seconds=total_duration,
            error_message=str(e),
        )


def select_config(
    metrics: QualityMetrics,
    user_config: EnhancementConfig,
) -> EnhancementConfig:
    """Select appropriate enhancement config based on quality metrics.

    Chooses between minimal, light, standard, and aggressive processing
    based on the input audio quality.

    Args:
        metrics: Quality metrics from input analysis.
        user_config: User-provided base configuration.

    Returns:
        Adjusted EnhancementConfig.
    """
    if metrics.is_excellent_quality:
        # Excellent quality input - use minimal processing to preserve quality
        config = EnhancementConfig.minimal()
    elif metrics.is_high_quality:
        # High quality input - use light processing
        config = EnhancementConfig.light()
    elif metrics.needs_ai_enhancement:
        # Poor quality input - use aggressive processing
        config = EnhancementConfig.aggressive()
    else:
        # Medium quality - use standard processing
        config = EnhancementConfig.standard()

    # Preserve user overrides
    if user_config.target_loudness_lufs != -14.0:
        config.target_loudness_lufs = user_config.target_loudness_lufs

    # Honor explicit disable flags from user
    if not user_config.ai_enhancement_enabled:
        config.ai_enhancement_enabled = False

    if user_config.preserve_dynamics:
        config.preserve_dynamics = True

    return config
