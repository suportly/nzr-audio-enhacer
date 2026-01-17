"""ProcessingResult data class for enhancement outcomes."""

from dataclasses import dataclass, field
from typing import Optional

from .audio_file import AudioFile
from .metrics import QualityMetrics
from .stage import ProcessingStage


@dataclass
class ProcessingResult:
    """Outcome of the enhancement process.

    Attributes:
        success: Whether processing completed successfully.
        input_file: Original input file metadata.
        output_file: Enhanced output file metadata (None if failed).
        input_metrics: Quality metrics before processing.
        output_metrics: Quality metrics after processing (None if failed).
        processing_stages: List of applied processing steps.
        duration_seconds: Total processing time.
        error_message: Error details if failed.
    """

    success: bool
    input_file: AudioFile
    output_file: Optional[AudioFile] = None
    input_metrics: Optional[QualityMetrics] = None
    output_metrics: Optional[QualityMetrics] = None
    processing_stages: list[ProcessingStage] = field(default_factory=list)
    duration_seconds: float = 0.0
    error_message: Optional[str] = None

    @property
    def quality_improved(self) -> bool:
        """Check if quality was improved during processing."""
        if not self.success or not self.input_metrics or not self.output_metrics:
            return False
        return self.output_metrics.quality_score > self.input_metrics.quality_score

    @property
    def snr_improvement_db(self) -> float:
        """Calculate SNR improvement in decibels."""
        if not self.input_metrics or not self.output_metrics:
            return 0.0
        return self.output_metrics.snr_db - self.input_metrics.snr_db

    @property
    def quality_improvement_percent(self) -> float:
        """Calculate quality improvement as a percentage."""
        if not self.input_metrics or not self.output_metrics:
            return 0.0
        if self.input_metrics.quality_score == 0:
            return 0.0
        improvement = self.output_metrics.quality_score - self.input_metrics.quality_score
        return (improvement / self.input_metrics.quality_score) * 100

    @property
    def ai_was_used(self) -> bool:
        """Check if AI enhancement was used in any stage."""
        ai_methods = {"deepfilternet", "ai", "neural"}
        for stage in self.processing_stages:
            if stage.enabled and any(m in stage.method.lower() for m in ai_methods):
                return True
        return False

    @classmethod
    def failure(cls, input_file: AudioFile, error_message: str) -> "ProcessingResult":
        """Create a failure result.

        Args:
            input_file: The input file that failed to process.
            error_message: Description of the error.

        Returns:
            ProcessingResult indicating failure.
        """
        return cls(
            success=False,
            input_file=input_file,
            error_message=error_message,
        )
