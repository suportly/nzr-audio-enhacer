# Tasks: Music Quality Enhancer

**Input**: Design documents from `/specs/001-music-quality-enhancer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification. Tests are included as optional guidance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Python package structure

- [x] T001 Create project structure per implementation plan (src/, tests/, src/models/, src/services/, src/utils/)
- [x] T002 Create pyproject.toml with project metadata and dependencies (deepfilternet, librosa, scipy, soundfile, noisereduce, click, tqdm)
- [x] T003 [P] Create requirements.txt with runtime dependencies
- [x] T004 [P] Create requirements-dev.txt with development dependencies (pytest, pytest-cov, black, ruff)
- [x] T005 [P] Create src/__init__.py with package version
- [x] T006 [P] Configure CLI entry point in pyproject.toml (enhance-audio command)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and utilities that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 [P] Create AudioFile dataclass in src/models/audio_file.py with fields: path, format, sample_rate, bit_depth, channels, duration, samples
- [x] T008 [P] Create QualityMetrics dataclass in src/models/metrics.py with fields: snr_db, spectral_flatness, dynamic_range_db, clipping_ratio, silence_ratio, quality_score
- [x] T009 [P] Create EnhancementConfig dataclass in src/models/config.py with fields: noise_reduction_strength, eq_enabled, dynamics_enabled, ai_enhancement_enabled, preserve_dynamics, target_loudness_lufs
- [x] T010 [P] Create ProcessingResult dataclass in src/models/result.py with fields: success, input_file, output_file, input_metrics, output_metrics, processing_stages, duration_seconds, error_message
- [x] T011 [P] Create ProcessingStage dataclass in src/models/stage.py with fields: name, enabled, method, parameters, duration_seconds
- [x] T012 Create src/models/__init__.py exporting all dataclasses
- [x] T013 Create error types module in src/models/errors.py with custom exceptions (InvalidFormatError, FileNotFoundError, FileCorruptedError, UnsupportedChannelsError, InsufficientSpaceError, ProcessingFailedError, ModelUnavailableError)
- [x] T014 [P] Create loader service in src/services/loader.py with functions: load_audio(path) -> AudioFile, validate_wav_format(path) -> bool
- [x] T015 Create exporter service in src/services/exporter.py with functions: save_audio(audio_file, path) -> bool, generate_output_path(input_path, suffix="_enhanced") -> str

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Audio Enhancement (Priority: P1) MVP

**Goal**: Accept .wav files, apply traditional DSP enhancement (noise reduction, EQ, dynamics), output enhanced .wav

**Independent Test**: Run `enhance-audio noisy_file.wav` and verify output file has reduced noise and improved quality metrics

### Implementation for User Story 1

- [x] T016 [US1] Implement quality analyzer in src/services/analyzer.py with functions: analyze_quality(audio_file) -> QualityMetrics, estimate_snr(samples, sr) -> float, calculate_spectral_flatness(samples, sr) -> float, calculate_dynamic_range(samples) -> float
- [x] T017 [US1] Implement spectral gating noise reduction in src/services/noise_reduction.py with function: reduce_noise_spectral(audio_file, strength) -> ndarray (using noisereduce library)
- [x] T018 [US1] Implement spectral enhancement (EQ) in src/services/spectral.py with functions: apply_eq(samples, sr, config) -> ndarray, enhance_clarity(samples, sr) -> ndarray (using scipy filters)
- [x] T019 [US1] Implement dynamic range processing in src/services/dynamics.py with functions: compress_dynamics(samples, config) -> ndarray, normalize_loudness(samples, target_lufs) -> ndarray
- [x] T020 [US1] Create enhancement pipeline orchestrator in src/services/enhancer.py with function: enhance_audio(audio_file, config) -> ProcessingResult that chains: analyze -> noise_reduce -> eq -> dynamics -> validate
- [x] T021 [US1] Implement quality-based config selection in src/services/enhancer.py with function: select_config(metrics, user_config) -> EnhancementConfig (auto selects light/standard/aggressive)
- [x] T022 [US1] Create basic CLI in src/cli.py with click: enhance-audio INPUT_FILE --output --quality --preserve-dynamics --loudness --help --version
- [x] T023 [US1] Add input validation to CLI: check file exists, is .wav format, show clear error messages per contracts/cli-interface.md
- [x] T024 [US1] Add output formatting to CLI: display analysis results, completion message with quality improvement stats
- [x] T025 [US1] Implement --dry-run flag in CLI to analyze without processing

**Checkpoint**: Basic enhancement works. Can process .wav files with traditional DSP. MVP complete.

---

## Phase 4: User Story 2 - AI-Powered Enhancement (Priority: P2)

**Goal**: Integrate DeepFilterNet for heavy noise reduction and artifact removal when quality_score < 0.5

**Independent Test**: Run `enhance-audio heavily_noisy_file.wav` and verify AI enhancement is triggered with superior results compared to spectral gating alone

### Implementation for User Story 2

- [x] T026 [US2] Implement AI model manager in src/services/ai_models.py with functions: load_deepfilternet() -> model, is_model_available() -> bool, get_model_path() -> str
- [x] T027 [US2] Implement AI-based noise reduction in src/services/noise_reduction.py with function: reduce_noise_ai(audio_file) -> ndarray (using DeepFilterNet)
- [x] T028 [US2] Add fallback logic in src/services/noise_reduction.py: try AI enhancement, fallback to spectral gating if model unavailable
- [x] T029 [US2] Update enhancer.py to select AI vs traditional based on QualityMetrics.needs_ai_enhancement property
- [x] T030 [US2] Implement --no-ai CLI flag to force traditional processing only
- [x] T031 [US2] Add model download command or auto-download on first use in src/services/ai_models.py
- [x] T032 [US2] Update CLI output to indicate when AI enhancement was used vs traditional

**Checkpoint**: AI enhancement works for low-quality inputs. System intelligently selects processing method.

---

## Phase 5: User Story 3 - Processing Progress Feedback (Priority: P3)

**Goal**: Display progress bars and stage information during processing for better UX

**Independent Test**: Run `enhance-audio large_file.wav` and verify progress bar updates throughout processing with stage names

### Implementation for User Story 3

- [x] T033 [P] [US3] Create progress reporter utility in src/utils/progress.py with class: ProgressReporter with methods: start_stage(name), update(percentage), complete_stage()
- [x] T034 [US3] Integrate tqdm progress bars in src/utils/progress.py for visual feedback
- [x] T035 [US3] Update enhancer.py to report progress at each pipeline stage (analyzing, noise_reduction, spectral, dynamics, exporting)
- [x] T036 [US3] Update CLI to pass progress reporter to enhancer and display stage names
- [x] T037 [US3] Implement --verbose flag for detailed progress (per-stage timing, parameter values)
- [x] T038 [US3] Implement --quiet flag to suppress progress output (errors only)
- [x] T039 [US3] Add estimated time remaining calculation in progress reporter

**Checkpoint**: Progress feedback works. Users see processing progress and stage information.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T040 [P] Implement --json flag for machine-readable output per contracts/cli-interface.md
- [x] T041 [P] Add environment variable support (ENHANCE_AUDIO_MODEL_PATH, ENHANCE_AUDIO_WORKERS, ENHANCE_AUDIO_LOG_LEVEL)
- [x] T042 Add exit codes per CLI contract (0=success, 1=invalid args, 2=not found, 3=invalid format, 4=processing failed, 5=write failed)
- [x] T043 [P] Create test fixtures directory with sample .wav files in tests/fixtures/
- [x] T044 [P] Create pytest configuration in tests/conftest.py with audio fixtures
- [x] T045 Run quickstart.md validation: verify installation steps work, basic usage works
- [x] T046 Final code cleanup and docstrings

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - MVP
- **User Story 2 (Phase 4)**: Depends on Foundational, can integrate with US1
- **User Story 3 (Phase 5)**: Depends on Foundational, integrates with US1/US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends noise_reduction.py from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with enhancer.py from US1

### Within Each User Story

- Models/utilities before services
- Services before CLI integration
- Core implementation before optional flags

### Parallel Opportunities

**Phase 1 (Setup)**:
```
Parallel: T003, T004, T005, T006
```

**Phase 2 (Foundational)**:
```
Parallel: T007, T008, T009, T010, T011 (all dataclasses)
Then: T012 (exports), T013 (errors)
Parallel: T014, T015 (loader, exporter)
```

**Phase 3 (US1)** - after Foundational:
```
Sequential: T016 -> T017 -> T018 -> T019 -> T020 -> T021
Then: T022 -> T023 -> T024 -> T025
```

**Phase 4 (US2)** - can start after Foundational, best after US1:
```
Sequential: T026 -> T027 -> T028 -> T029 -> T030 -> T031 -> T032
```

**Phase 5 (US3)** - can start after Foundational:
```
T033 (parallel, no dependencies)
Then: T034 -> T035 -> T036 -> T037 -> T038 -> T039
```

**Phase 6 (Polish)**:
```
Parallel: T040, T041, T043, T044
Then: T042, T045, T046
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all dataclass models together:
Task: "Create AudioFile dataclass in src/models/audio_file.py"
Task: "Create QualityMetrics dataclass in src/models/metrics.py"
Task: "Create EnhancementConfig dataclass in src/models/config.py"
Task: "Create ProcessingResult dataclass in src/models/result.py"
Task: "Create ProcessingStage dataclass in src/models/stage.py"

# After all complete, launch services together:
Task: "Create loader service in src/services/loader.py"
Task: "Create exporter service in src/services/exporter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Basic Enhancement
4. **STOP and VALIDATE**: Test with real .wav files
5. Deploy/demo if ready - users can enhance audio with traditional DSP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP - traditional enhancement)
3. Add User Story 2 → Test independently → Deploy (AI enhancement added)
4. Add User Story 3 → Test independently → Deploy (progress feedback added)
5. Each story adds value without breaking previous stories

### Suggested Execution Order

1. **T001-T006**: Setup phase (can parallelize T003-T006)
2. **T007-T015**: Foundational phase (can parallelize dataclasses, then services)
3. **T016-T025**: User Story 1 - Core enhancement MVP
4. **T026-T032**: User Story 2 - AI enhancement (optional, can skip for simpler MVP)
5. **T033-T039**: User Story 3 - Progress feedback (optional, improves UX)
6. **T040-T046**: Polish phase

---

## Notes

- [P] tasks = different files, no dependencies, can run simultaneously
- [Story] label maps task to specific user story for traceability
- MVP is achievable with just Setup + Foundational + User Story 1 (T001-T025)
- AI enhancement (US2) can be deferred if DeepFilterNet setup is complex
- Progress feedback (US3) is pure UX improvement, can be added anytime
- Commit after each task or logical group
- Test with real .wav files at each checkpoint
