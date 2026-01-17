# Quickstart: Music Quality Enhancer

**Feature Branch**: `001-music-quality-enhancer`
**Date**: 2026-01-16

## Prerequisites

- Python 3.11 or higher
- pip package manager
- ~2GB disk space for AI models (downloaded on first run)
- Recommended: 8GB RAM for processing longer files

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd nzr-music-enhancer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
enhance-audio --version
```

## Quick Usage

### Enhance a Single File

```bash
# Basic enhancement (auto-detects quality level)
enhance-audio my_song.wav

# Output: my_song_enhanced.wav
```

### Specify Output Location

```bash
enhance-audio recording.wav -o output/enhanced_recording.wav
```

### Check Quality Without Processing

```bash
enhance-audio recording.wav --dry-run
```

## Common Scenarios

### Scenario 1: Noisy Recording

```bash
# Use aggressive processing for heavily degraded audio
enhance-audio noisy_podcast.wav -q aggressive
```

### Scenario 2: Already Good Quality

```bash
# Use light processing to avoid over-processing
enhance-audio studio_master.wav -q light
```

### Scenario 3: Batch Processing

```bash
# Process all WAV files in a directory
for file in input/*.wav; do
  enhance-audio "$file" -o "output/$(basename "$file")"
done
```

### Scenario 4: Maximum Control

```bash
# Disable AI, set custom loudness target
enhance-audio track.wav --no-ai -l -16.0 -v
```

## Understanding Output

After processing, you'll see:

```
Analyzing: my_song.wav
  Format: WAV, 44100 Hz, 16-bit, stereo
  Duration: 3:24
  Quality: Medium (score: 0.52)

Processing: [████████████████████] 100%

Complete: my_song_enhanced.wav
  Quality improved: 0.52 → 0.87 (+67%)
```

**Quality Score Interpretation**:
- 0.0 - 0.3: Poor quality, needs significant enhancement
- 0.3 - 0.6: Medium quality, standard processing recommended
- 0.6 - 0.8: Good quality, light processing sufficient
- 0.8 - 1.0: Excellent quality, minimal processing applied

## Troubleshooting

### "Model not found" Error

AI models are downloaded automatically on first run. If download fails:

```bash
# Set custom model path via environment variable
export ENHANCE_AUDIO_MODEL_PATH=/path/to/models

# Or disable AI enhancement to use traditional processing
enhance-audio file.wav --no-ai
```

### Out of Memory

For long audio files (>30 minutes):

```bash
# Process in chunks (automatic, but can be forced)
ENHANCE_AUDIO_WORKERS=1 enhance-audio long_recording.wav
```

### Processing Takes Too Long

```bash
# Disable AI for faster (but less effective) processing
enhance-audio file.wav --no-ai
```

## Next Steps

- Read the [CLI Interface Contract](contracts/cli-interface.md) for all options
- Review the [Data Model](data-model.md) for understanding internal processing
- Check the [Specification](spec.md) for feature requirements

## Getting Help

```bash
# Show all options
enhance-audio --help

# Show version
enhance-audio --version
```
