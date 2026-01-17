"""Command-line interface for the music enhancer."""

import json
import os
import sys
from pathlib import Path

import click

from src import __version__
from src.models import (
    AudioFileNotFoundError,
    EnhancementConfig,
    EnhancerError,
    InvalidFormatError,
    ProcessingResult,
    QualityLevel,
)
from src.services.analyzer import analyze_quality
from src.services.enhancer import enhance_audio
from src.services.loader import load_audio, validate_wav_format

# Exit codes per CLI contract
EXIT_SUCCESS = 0
EXIT_INVALID_ARGS = 1
EXIT_NOT_FOUND = 2
EXIT_INVALID_FORMAT = 3
EXIT_PROCESSING_FAILED = 4
EXIT_WRITE_FAILED = 5


@click.command()
@click.argument("input_file", type=click.Path(exists=False))
@click.option(
    "-o", "--output",
    type=click.Path(),
    default=None,
    help="Output file path. Defaults to {input}_enhanced.wav",
)
@click.option(
    "-q", "--quality",
    type=click.Choice(["auto", "light", "standard", "aggressive"]),
    default="auto",
    help="Processing intensity level.",
)
@click.option(
    "--no-ai",
    is_flag=True,
    default=False,
    help="Disable AI-based enhancement.",
)
@click.option(
    "-d", "--preserve-dynamics",
    is_flag=True,
    default=True,
    help="Avoid over-compression (default: enabled).",
)
@click.option(
    "-l", "--loudness",
    type=float,
    default=-14.0,
    help="Target loudness in LUFS (default: -14.0).",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Show detailed progress information.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress all output except errors.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output results as JSON.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Analyze without processing.",
)
@click.version_option(version=__version__, prog_name="enhance-audio")
def main(
    input_file: str,
    output: str | None,
    quality: str,
    no_ai: bool,
    preserve_dynamics: bool,
    loudness: float,
    verbose: bool,
    quiet: bool,
    json_output: bool,
    dry_run: bool,
) -> None:
    """Enhance audio quality of WAV files.

    INPUT_FILE: Path to the input .wav file to enhance.

    Examples:

        enhance-audio recording.wav

        enhance-audio recording.wav -o enhanced/recording.wav

        enhance-audio noisy.wav -q aggressive

        enhance-audio master.wav -q light --dry-run
    """
    # Load environment variables
    _load_env_config()

    try:
        # Validate input file
        input_path = Path(input_file)

        if not input_path.exists():
            raise AudioFileNotFoundError(str(input_path))

        validate_wav_format(input_path)

        # Load audio
        if not quiet and not json_output:
            click.echo(f"Analyzing: {input_path.name}")

        audio_file = load_audio(input_path)

        # Display input info
        if not quiet and not json_output:
            _display_audio_info(audio_file)

        # Analyze quality
        metrics = analyze_quality(audio_file)

        if not quiet and not json_output:
            _display_quality_info(metrics)

        # Dry run mode - just analyze
        if dry_run:
            if json_output:
                _output_dry_run_json(audio_file, metrics, quality, no_ai)
            else:
                _display_dry_run_info(metrics, quality, no_ai)
            return

        # Build config
        config = _build_config(quality, no_ai, preserve_dynamics, loudness)

        # Process audio
        if not quiet and not json_output:
            click.echo()
            click.echo("Processing...")

        result = enhance_audio(audio_file, config, output)

        if not result.success:
            if json_output:
                _output_error_json(result.error_message or "Processing failed")
            else:
                click.echo(f"Error: {result.error_message}", err=True)
            sys.exit(EXIT_PROCESSING_FAILED)

        # Display results
        if json_output:
            _output_result_json(result)
        elif not quiet:
            _display_results(result, verbose)

    except AudioFileNotFoundError as e:
        if json_output:
            _output_error_json(e.message)
        else:
            click.echo(f"Error: {e.message}", err=True)
        sys.exit(EXIT_NOT_FOUND)
    except InvalidFormatError as e:
        if json_output:
            _output_error_json(e.message)
        else:
            click.echo(f"Error: {e.message}", err=True)
        sys.exit(EXIT_INVALID_FORMAT)
    except EnhancerError as e:
        if json_output:
            _output_error_json(e.message)
        else:
            click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        if json_output:
            _output_error_json(str(e))
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_PROCESSING_FAILED)


def _load_env_config() -> None:
    """Load configuration from environment variables."""
    # ENHANCE_AUDIO_MODEL_PATH is handled in ai_models.py
    # ENHANCE_AUDIO_WORKERS - not yet implemented
    # ENHANCE_AUDIO_LOG_LEVEL - not yet implemented
    pass


def _display_audio_info(audio_file) -> None:
    """Display audio file information."""
    duration_min = int(audio_file.duration // 60)
    duration_sec = int(audio_file.duration % 60)

    channel_str = "mono" if audio_file.is_mono else "stereo"

    click.echo(f"  Format: WAV, {audio_file.sample_rate} Hz, "
               f"{audio_file.bit_depth}-bit, {channel_str}")
    click.echo(f"  Duration: {duration_min}:{duration_sec:02d}")


def _display_quality_info(metrics) -> None:
    """Display quality analysis information."""
    click.echo(f"  Quality: {metrics.quality_level} (score: {metrics.quality_score:.2f})")


def _display_dry_run_info(metrics, quality: str, no_ai: bool) -> None:
    """Display dry run analysis information."""
    click.echo()
    click.echo("Recommended processing:")

    # Determine effective quality level
    if quality == "auto":
        if metrics.is_excellent_quality:
            effective_quality = "minimal"
        elif metrics.is_high_quality:
            effective_quality = "light"
        elif metrics.needs_ai_enhancement:
            effective_quality = "aggressive"
        else:
            effective_quality = "standard"
    else:
        effective_quality = quality

    click.echo(f"  Level: {effective_quality}")

    # Stages depend on quality level
    if effective_quality == "minimal":
        stages = ["noise_reduction"]
    else:
        stages = ["noise_reduction", "spectral_enhancement", "dynamic_optimization"]
    click.echo(f"  Stages: {', '.join(stages)}")

    ai_recommended = metrics.needs_ai_enhancement and not no_ai
    ai_str = "recommended" if ai_recommended else "not needed" if not no_ai else "disabled"
    click.echo(f"  AI enhancement: {ai_str}")

    click.echo()
    click.echo(click.style("No changes made (dry run).", fg="yellow"))


def _output_dry_run_json(audio_file, metrics, quality: str, no_ai: bool) -> None:
    """Output dry run analysis as JSON."""
    result = {
        "success": True,
        "dry_run": True,
        "input": {
            "path": str(audio_file.path),
            "format": audio_file.format,
            "sample_rate": audio_file.sample_rate,
            "bit_depth": audio_file.bit_depth,
            "channels": audio_file.channels,
            "duration_seconds": audio_file.duration,
        },
        "metrics": {
            "quality_score": metrics.quality_score,
            "quality_level": metrics.quality_level,
            "snr_db": metrics.snr_db,
            "needs_ai_enhancement": metrics.needs_ai_enhancement,
        },
        "recommended": {
            "quality_level": quality if quality != "auto" else (
                "minimal" if metrics.is_excellent_quality else
                "light" if metrics.is_high_quality else
                "aggressive" if metrics.needs_ai_enhancement else
                "standard"
            ),
            "ai_enhancement": metrics.needs_ai_enhancement and not no_ai,
        },
    }
    click.echo(json.dumps(result, indent=2))


def _build_config(
    quality: str,
    no_ai: bool,
    preserve_dynamics: bool,
    loudness: float,
) -> EnhancementConfig:
    """Build enhancement config from CLI options."""
    quality_level = QualityLevel(quality)

    if quality == "light":
        config = EnhancementConfig.light()
    elif quality == "standard":
        config = EnhancementConfig.standard()
    elif quality == "aggressive":
        config = EnhancementConfig.aggressive()
    else:  # auto
        config = EnhancementConfig()
        config.quality_level = QualityLevel.AUTO

    # Apply user overrides
    config.ai_enhancement_enabled = not no_ai
    config.preserve_dynamics = preserve_dynamics
    config.target_loudness_lufs = loudness

    return config


def _display_results(result, verbose: bool) -> None:
    """Display processing results."""
    click.echo()

    # Stage summary
    for stage in result.processing_stages:
        if stage.enabled:
            status = click.style("done", fg="green")
            # Show AI indicator for noise reduction
            if stage.name == "noise_reduction" and stage.parameters.get("ai_used"):
                status += click.style(" (AI)", fg="cyan")
            if verbose:
                status += f" ({stage.duration_seconds:.2f}s)"
        else:
            status = click.style("skipped", fg="yellow")

        click.echo(f"  {stage.name}: {status}")

    click.echo()
    click.echo(click.style(f"Complete: {result.output_file.path.name}", fg="green", bold=True))

    # Quality improvement stats
    if result.input_metrics and result.output_metrics:
        improvement = result.quality_improvement_percent
        input_score = result.input_metrics.quality_score
        output_score = result.output_metrics.quality_score

        click.echo(f"  Quality improved: {input_score:.2f} → {output_score:.2f} "
                   f"({improvement:+.0f}%)")

        snr_improvement = result.snr_improvement_db
        click.echo(f"  SNR: {result.input_metrics.snr_db:.0f} dB → "
                   f"{result.output_metrics.snr_db:.0f} dB "
                   f"({snr_improvement:+.0f} dB)")

    # Processing time
    duration_min = int(result.duration_seconds // 60)
    duration_sec = result.duration_seconds % 60
    if duration_min > 0:
        click.echo(f"  Processing time: {duration_min}m {duration_sec:.0f}s")
    else:
        click.echo(f"  Processing time: {duration_sec:.1f}s")


def _output_result_json(result: ProcessingResult) -> None:
    """Output processing result as JSON."""
    output = {
        "success": result.success,
        "input": {
            "path": str(result.input_file.path),
            "format": result.input_file.format,
            "sample_rate": result.input_file.sample_rate,
            "bit_depth": result.input_file.bit_depth,
            "channels": result.input_file.channels,
            "duration_seconds": result.input_file.duration,
        },
        "output": {
            "path": str(result.output_file.path) if result.output_file else None,
            "format": result.output_file.format if result.output_file else None,
            "sample_rate": result.output_file.sample_rate if result.output_file else None,
            "bit_depth": result.output_file.bit_depth if result.output_file else None,
            "channels": result.output_file.channels if result.output_file else None,
            "duration_seconds": result.output_file.duration if result.output_file else None,
        },
        "metrics": {
            "input_quality_score": result.input_metrics.quality_score if result.input_metrics else None,
            "output_quality_score": result.output_metrics.quality_score if result.output_metrics else None,
            "snr_improvement_db": result.snr_improvement_db,
        },
        "processing": {
            "stages": [s.name for s in result.processing_stages if s.enabled],
            "ai_used": result.ai_was_used,
            "duration_seconds": result.duration_seconds,
        },
    }
    click.echo(json.dumps(output, indent=2))


def _output_error_json(message: str) -> None:
    """Output error as JSON."""
    output = {
        "success": False,
        "error": message,
    }
    click.echo(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
