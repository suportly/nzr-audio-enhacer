# CLI Interface Contract: Music Quality Enhancer

**Feature Branch**: `001-music-quality-enhancer`
**Date**: 2026-01-16

## Command Overview

The music quality enhancer is a command-line tool that accepts .wav files and outputs enhanced audio.

## Usage

```bash
enhance-audio INPUT_FILE [OPTIONS]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| INPUT_FILE | Yes | Path to input .wav file |

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --output | -o | PATH | {input}_enhanced.wav | Output file path |
| --quality | -q | CHOICE | auto | Processing intensity: auto, light, standard, aggressive |
| --no-ai | | FLAG | False | Disable AI-based enhancement |
| --preserve-dynamics | -d | FLAG | True | Avoid over-compression |
| --loudness | -l | FLOAT | -14.0 | Target loudness in LUFS |
| --verbose | -v | FLAG | False | Show detailed progress |
| --quiet | | FLAG | False | Suppress all output except errors |
| --json | | FLAG | False | Output results as JSON |
| --dry-run | | FLAG | False | Analyze without processing |
| --version | | FLAG | - | Show version and exit |
| --help | -h | FLAG | - | Show help message |

## Quality Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| auto | Analyze input and select appropriate level | Default, recommended |
| light | Minimal processing, preserve original character | High-quality inputs |
| standard | Balanced noise reduction and enhancement | Average quality inputs |
| aggressive | Maximum enhancement, AI-enabled | Poor quality inputs |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Input file not found |
| 3 | Invalid input format |
| 4 | Processing failed |
| 5 | Output write failed |

## Standard Output

### Normal Mode (default)

```
Analyzing: song.wav
  Format: WAV, 44100 Hz, 16-bit, stereo
  Duration: 3:24
  Quality: Medium (score: 0.52)

Processing: [████████████████████] 100%
  Stage 1/3: Noise reduction... done
  Stage 2/3: Spectral enhancement... done
  Stage 3/3: Dynamic optimization... done

Complete: song_enhanced.wav
  Quality improved: 0.52 → 0.87 (+67%)
  SNR: 18 dB → 32 dB
  Processing time: 1m 23s
```

### Verbose Mode (--verbose)

Adds per-stage timing, parameter values, and intermediate metrics.

### JSON Mode (--json)

```json
{
  "success": true,
  "input": {
    "path": "/path/to/song.wav",
    "format": "wav",
    "sample_rate": 44100,
    "bit_depth": 16,
    "channels": 2,
    "duration_seconds": 204.5
  },
  "output": {
    "path": "/path/to/song_enhanced.wav",
    "format": "wav",
    "sample_rate": 44100,
    "bit_depth": 24,
    "channels": 2,
    "duration_seconds": 204.5
  },
  "metrics": {
    "input_quality_score": 0.52,
    "output_quality_score": 0.87,
    "snr_improvement_db": 14.0
  },
  "processing": {
    "stages": ["noise_reduction", "spectral_enhancement", "dynamic_optimization"],
    "ai_used": true,
    "duration_seconds": 83.2
  }
}
```

### Dry Run Mode (--dry-run)

```
Analysis: song.wav
  Format: WAV, 44100 Hz, 16-bit, stereo
  Duration: 3:24
  Quality: Medium (score: 0.52)

Recommended processing:
  Level: standard
  Stages: noise_reduction, spectral_enhancement, dynamic_optimization
  AI enhancement: recommended
  Estimated time: ~1-2 minutes

No changes made (dry run).
```

## Standard Error

All errors are written to stderr:

```
Error: Input file not found: song.wav
Error: Invalid format - expected WAV, got MP3
Error: Processing failed: insufficient memory
```

## Examples

### Basic Usage

```bash
# Enhance with default settings
enhance-audio recording.wav

# Specify output path
enhance-audio recording.wav -o enhanced/recording.wav

# Light processing for high-quality input
enhance-audio master.wav -q light

# Aggressive processing without AI
enhance-audio noisy_recording.wav -q aggressive --no-ai
```

### Scripting

```bash
# Process multiple files
for f in *.wav; do
  enhance-audio "$f" -o "enhanced/$f" --json >> results.json
done

# Check quality without processing
enhance-audio recording.wav --dry-run --json | jq '.metrics.input_quality_score'
```

### Integration

```bash
# Use with other tools
enhance-audio input.wav -o - | ffmpeg -i - output.mp3  # (future: stdout support)

# CI/CD pipeline
enhance-audio test_audio.wav --json || exit 1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ENHANCE_AUDIO_MODEL_PATH | Custom path for AI models | ~/.cache/enhance-audio/models |
| ENHANCE_AUDIO_WORKERS | Number of processing threads | auto (CPU count) |
| ENHANCE_AUDIO_LOG_LEVEL | Logging verbosity | INFO |
