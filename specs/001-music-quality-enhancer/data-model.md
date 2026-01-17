# Data Model: Music Quality Enhancer

**Feature Branch**: `001-music-quality-enhancer`
**Date**: 2026-01-16

## Overview

This document defines the data structures and entities used by the Music Quality Enhancer system. The system operates on audio files and produces enhanced output without persistent storage.

## Core Entities

### AudioFile

Represents an input or output audio file.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| path | string | Absolute file path | Must exist for input, parent dir must exist for output |
| format | string | Audio format identifier | Must be "wav" for input |
| sample_rate | integer | Samples per second | Common: 44100, 48000, 96000 Hz |
| bit_depth | integer | Bits per sample | Common: 16, 24, 32 |
| channels | integer | Number of audio channels | 1 (mono) or 2 (stereo) |
| duration | float | Length in seconds | > 0 |
| samples | ndarray | Raw audio data as numpy array | Shape: (samples,) or (samples, channels) |

**Validation Rules**:
- File must be readable and valid .wav format
- Sample rate must be > 0
- Bit depth must be 8, 16, 24, or 32
- Channels must be 1 or 2 (multichannel not supported in v1)

---

### QualityMetrics

Assessment of audio quality used to determine processing intensity.

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| snr_db | float | Estimated signal-to-noise ratio | -inf to +inf dB |
| spectral_flatness | float | Measure of noise-like vs tonal | 0.0 to 1.0 |
| dynamic_range_db | float | Peak to RMS difference | 0 to 100+ dB |
| clipping_ratio | float | Percentage of clipped samples | 0.0 to 1.0 |
| silence_ratio | float | Percentage of silent sections | 0.0 to 1.0 |
| quality_score | float | Overall quality assessment | 0.0 (poor) to 1.0 (excellent) |

**Derived State**:
- `needs_ai_enhancement`: quality_score < 0.5 or snr_db < 20
- `is_high_quality`: quality_score > 0.8

---

### EnhancementConfig

Configuration parameters for the enhancement pipeline.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| noise_reduction_strength | float | Intensity of noise reduction | 0.5 (0.0-1.0) |
| eq_enabled | boolean | Apply equalization | True |
| dynamics_enabled | boolean | Apply dynamic range processing | True |
| ai_enhancement_enabled | boolean | Use AI models if needed | True |
| preserve_dynamics | boolean | Avoid over-compression | True |
| target_loudness_lufs | float | Target integrated loudness | -14.0 LUFS |

---

### ProcessingResult

Outcome of the enhancement process.

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Whether processing completed |
| input_file | AudioFile | Original input file metadata |
| output_file | AudioFile | Enhanced output file metadata |
| input_metrics | QualityMetrics | Quality before processing |
| output_metrics | QualityMetrics | Quality after processing |
| processing_stages | list[ProcessingStage] | Applied processing steps |
| duration_seconds | float | Total processing time |
| error_message | string | Error details if failed |

---

### ProcessingStage

Individual step in the enhancement pipeline.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Stage identifier (e.g., "noise_reduction") |
| enabled | boolean | Whether stage was executed |
| method | string | Technique used (e.g., "deepfilternet", "spectral_gating") |
| parameters | dict | Parameters applied |
| duration_seconds | float | Time taken for this stage |

---

## State Transitions

### Processing Pipeline Flow

```
INPUT_VALIDATION
    ├─ invalid → ERROR (invalid_file)
    └─ valid → QUALITY_ANALYSIS

QUALITY_ANALYSIS
    └─ analyzed → PROCESSING_DECISION

PROCESSING_DECISION
    ├─ high_quality → LIGHT_PROCESSING
    ├─ medium_quality → STANDARD_PROCESSING
    └─ low_quality → AI_ENHANCEMENT

LIGHT_PROCESSING
    └─ complete → OUTPUT_VALIDATION

STANDARD_PROCESSING
    └─ complete → OUTPUT_VALIDATION

AI_ENHANCEMENT
    ├─ success → OUTPUT_VALIDATION
    └─ fallback → STANDARD_PROCESSING

OUTPUT_VALIDATION
    ├─ improved → EXPORT
    └─ degraded → ROLLBACK_OR_WARN

EXPORT
    ├─ success → COMPLETE
    └─ failure → ERROR (export_failed)
```

---

## Data Flow

```
User provides: input_path, output_path (optional), config (optional)
                    │
                    ▼
            ┌───────────────┐
            │  Load Audio   │ → AudioFile (input)
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Analyze Audio │ → QualityMetrics (input)
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Select Config │ → EnhancementConfig (adapted)
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   Enhance     │ → AudioFile (processed samples)
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Validate Out  │ → QualityMetrics (output)
            └───────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Save Output  │ → ProcessingResult
            └───────────────┘
```

---

## File Naming Convention

**Default Output Naming**:
```
input:  /path/to/song.wav
output: /path/to/song_enhanced.wav
```

**With Custom Output**:
```
input:  /path/to/song.wav
output: /custom/path/enhanced_song.wav  (user-specified)
```

---

## Error Types

| Error Code | Description | User Message |
|------------|-------------|--------------|
| INVALID_FORMAT | Not a valid .wav file | "Input file is not a valid WAV file" |
| FILE_NOT_FOUND | Input path doesn't exist | "Input file not found: {path}" |
| FILE_CORRUPTED | File exists but can't be read | "Input file appears to be corrupted" |
| UNSUPPORTED_CHANNELS | More than 2 channels | "Only mono and stereo audio supported" |
| INSUFFICIENT_SPACE | Can't write output | "Insufficient disk space for output file" |
| PROCESSING_FAILED | Enhancement error | "Processing failed: {details}" |
| MODEL_UNAVAILABLE | AI model can't be loaded | "AI enhancement unavailable, using standard processing" |
