# NZR Music Enhancer

AI-powered audio quality enhancer for WAV files. Transform noisy recordings into professional-quality audio using intelligent processing that adapts to your input.

## Features

- **Quality-Adaptive Processing** - Automatically analyzes input and selects optimal processing intensity
- **AI-Powered Noise Reduction** - Uses DeepFilterNet neural network for superior noise removal
- **Spectral Enhancement** - EQ adjustments for warmth, presence, and clarity
- **Dynamic Range Optimization** - Compression and loudness normalization to industry standards
- **Non-Destructive** - Original files are never modified
- **Smart Preservation** - Excellent quality files receive minimal processing to preserve original sound

## Installation

### Requirements

- Python 3.11 or higher
- ~2GB disk space for AI models (downloaded on first run)

### Install

```bash
# Clone the repository
git clone https://github.com/suportly/nzr-audio-enhacer.git
cd nzr-audio-enhacer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .

# Verify installation
enhance-audio --version
```

## Usage

### Basic Enhancement

```bash
# Auto-detect quality and enhance
enhance-audio recording.wav

# Output: recording_enhanced.wav
```

### Specify Output

```bash
enhance-audio input.wav -o output/enhanced.wav
```

### Choose Processing Level

```bash
# Minimal - noise reduction only, preserves original EQ/dynamics
enhance-audio master.wav -q minimal

# Light - gentle processing for good quality files
enhance-audio podcast.wav -q light

# Standard - balanced processing for average quality
enhance-audio recording.wav -q standard

# Aggressive - heavy processing for poor quality files
enhance-audio noisy.wav -q aggressive
```

### Analyze Without Processing

```bash
enhance-audio recording.wav --dry-run
```

### Disable AI Enhancement

```bash
enhance-audio recording.wav --no-ai
```

### Machine-Readable Output

```bash
enhance-audio recording.wav --json
```

## CLI Options

```
Usage: enhance-audio [OPTIONS] INPUT_FILE

Options:
  -o, --output PATH          Output file path (default: {input}_enhanced.wav)
  -q, --quality LEVEL        Processing intensity:
                             - auto: automatically select based on quality
                             - minimal: noise reduction only
                             - light: gentle processing
                             - standard: balanced processing
                             - aggressive: heavy processing
  --no-ai                    Disable AI-based enhancement
  -d, --preserve-dynamics    Avoid over-compression (default: enabled)
  -l, --loudness FLOAT       Target loudness in LUFS (default: -14.0)
  -v, --verbose              Show detailed progress information
  --quiet                    Suppress all output except errors
  --json                     Output results as JSON
  --dry-run                  Analyze without processing
  --version                  Show version
  --help                     Show help message
```

## Quality Levels

| Level | Noise Reduction | EQ | Dynamics | Best For |
|-------|-----------------|-----|----------|----------|
| `minimal` | Light | No | No | Already mastered audio |
| `light` | Light | Yes | Yes | Good quality recordings |
| `standard` | Medium | Yes | Yes | Average recordings |
| `aggressive` | Heavy + AI | Yes | Yes | Noisy/poor quality |

When using `auto` (default), the tool analyzes your audio and selects:
- **Excellent quality (score > 0.8)**: minimal processing
- **Good quality (score 0.7-0.8)**: light processing
- **Medium quality (score 0.5-0.7)**: standard processing
- **Poor quality (score < 0.5)**: aggressive processing with AI

## Processing Pipeline

```
Input WAV
    │
    ▼
┌─────────────────┐
│ Quality Analysis │ ─── SNR, spectral flatness, dynamic range
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Noise Reduction │ ─── DeepFilterNet AI or spectral gating
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Spectral (EQ)   │ ─── Warmth, presence, clarity adjustments
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dynamics        │ ─── Compression + loudness normalization
└────────┬────────┘
         │
         ▼
   Output WAV
```

## Output Example

```
Analyzing: recording.wav
  Format: WAV, 44100 Hz, 16-bit, stereo
  Duration: 3:24
  Quality: Medium (score: 0.52)

Processing...

  analysis: done
  noise_reduction: done (AI)
  spectral: done
  dynamics: done
  validation: done
  export: done

Complete: recording_enhanced.wav
  Quality improved: 0.52 → 0.87 (+67%)
  SNR: 15 dB → 35 dB (+20 dB)
  Processing time: 45.2s
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ENHANCE_AUDIO_MODEL_PATH` | Custom path for AI models |

## Supported Formats

- **Input**: WAV (16-bit, 24-bit, 32-bit float)
- **Output**: WAV (24-bit)
- **Sample rates**: Any (commonly 44.1kHz, 48kHz, 96kHz)
- **Channels**: Mono and Stereo

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
