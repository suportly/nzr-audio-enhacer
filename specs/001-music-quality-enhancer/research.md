# Research: Music Quality Enhancer

**Feature Branch**: `001-music-quality-enhancer`
**Date**: 2026-01-16

## Executive Summary

This research evaluates the best tools and approaches for building a professional-grade audio enhancement script using Python. The recommended stack combines AI-based enhancement models with traditional DSP processing to achieve professional audio quality from .wav input files.

## Technology Decisions

### Decision 1: Programming Language

**Decision**: Python 3.11+

**Rationale**:
- Rich ecosystem of audio processing libraries
- Strong AI/ML support (PyTorch, TensorFlow)
- Cross-platform compatibility
- Easy CLI development with argparse/click
- Large community and documentation

**Alternatives Considered**:
- C++: Better performance but slower development cycle
- Rust: Growing audio ecosystem but less mature AI libraries
- JavaScript: Limited audio AI ecosystem

---

### Decision 2: AI Enhancement Engine

**Decision**: DeepFilterNet as primary AI engine with SpeechBrain as backup for complex cases

**Rationale**:
- DeepFilterNet provides real-time capable speech/music enhancement
- Apache 2.0 license allows commercial use
- Two-stage architecture handles both spectral envelope and periodic components
- Can run on CPU with reasonable performance
- SpeechBrain offers broader model selection for edge cases

**Alternatives Considered**:
- Facebook Denoiser: Excellent but more speech-focused
- AudioSR: Great for upscaling but doesn't address noise/artifacts
- Resemble Enhance: More speech-specific

---

### Decision 3: Traditional DSP Library

**Decision**: Librosa + SciPy for analysis, Noisereduce for lightweight noise reduction

**Rationale**:
- Librosa is industry standard for audio analysis
- SciPy provides robust filter design capabilities
- Noisereduce offers MIT-licensed spectral gating
- Avoids GPL-3 copyleft issues (Pedalboard)

**Alternatives Considered**:
- Pedalboard (Spotify): Excellent effects but GPL-3 license restrictions
- PyDub alone: Too high-level for professional processing

---

### Decision 4: Audio I/O

**Decision**: Soundfile for .wav I/O, PyDub for format flexibility

**Rationale**:
- Soundfile provides direct NumPy array access
- Preserves sample rate and bit depth accurately
- PyDub adds format conversion if needed in future

**Alternatives Considered**:
- Librosa load: Works but soundfile is more direct for .wav
- wave module: Too low-level

---

### Decision 5: Quality Detection

**Decision**: Custom analysis using Librosa metrics (SNR estimation, spectral flatness, dynamic range)

**Rationale**:
- No single library provides "quality scoring"
- Combine multiple metrics for intelligent processing decisions
- Prevents over-processing of high-quality input

**Alternatives Considered**:
- Fixed threshold processing: Risk of over-processing
- Manual user selection: Poor UX

---

### Decision 6: Processing Pipeline Architecture

**Decision**: Modular pipeline with quality-adaptive processing

**Rationale**:
- Analyze → Decide → Process → Verify approach
- Adjusts processing intensity based on input quality
- Separates concerns for maintainability
- Allows skipping unnecessary steps

**Processing Flow**:
```
1. Input Validation (.wav format, integrity)
2. Quality Analysis (SNR, spectral features, dynamic range)
3. Processing Decision (select appropriate enhancement level)
4. Enhancement Pipeline:
   a. Noise Reduction (AI-based if needed, spectral gating for light cases)
   b. Spectral Enhancement (EQ, clarity)
   c. Dynamic Range Optimization (compression, limiting)
5. Output Validation (quality improvement verification)
6. Export (preserve or improve specs)
```

---

## Technical Stack Summary

| Component | Library | License | Purpose |
|-----------|---------|---------|---------|
| Core Audio I/O | soundfile | BSD | Read/write .wav files |
| Audio Analysis | librosa | ISC | Feature extraction, quality metrics |
| Signal Processing | scipy | BSD | Filter design, spectral processing |
| AI Enhancement | deepfilternet | Apache 2.0 | Neural noise reduction |
| Light Noise Reduction | noisereduce | MIT | Spectral gating |
| CLI Interface | click | BSD | Command-line interface |
| Progress Display | tqdm | MIT | Progress bars |

---

## Licensing Compliance

All selected libraries are compatible with commercial use:
- No GPL-3 dependencies (avoided Pedalboard)
- Apache 2.0 provides patent protection
- MIT/BSD/ISC allow derivative works

---

## Performance Targets

Based on research:
- DeepFilterNet can achieve real-time on modern CPUs
- 3-minute audio file should process in under 5 minutes (per success criteria)
- Memory footprint manageable for consumer hardware

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| AI model download size | Document requirements, cache models |
| GPU not available | Ensure CPU fallback works |
| Unusual audio formats | Validate input strictly, provide clear errors |
| Over-processing | Implement quality detection, adaptive processing |

---

## References

- DeepFilterNet: https://github.com/Rikorose/DeepFilterNet
- Librosa: https://librosa.org/doc/
- SpeechBrain: https://speechbrain.github.io/
- Noisereduce: https://github.com/timsainb/noisereduce
- Soundfile: https://python-soundfile.readthedocs.io/
