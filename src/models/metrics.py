"""QualityMetrics data class for audio quality assessment."""

from dataclasses import dataclass


@dataclass
class QualityMetrics:
    """Assessment of audio quality used to determine processing intensity.

    Attributes:
        snr_db: Estimated signal-to-noise ratio in decibels.
        spectral_flatness: Measure of noise-like vs tonal content (0.0 to 1.0).
        dynamic_range_db: Peak to RMS difference in decibels.
        clipping_ratio: Percentage of clipped samples (0.0 to 1.0).
        silence_ratio: Percentage of silent sections (0.0 to 1.0).
        quality_score: Overall quality assessment (0.0 poor to 1.0 excellent).
    """

    snr_db: float
    spectral_flatness: float
    dynamic_range_db: float
    clipping_ratio: float
    silence_ratio: float
    quality_score: float

    @property
    def needs_ai_enhancement(self) -> bool:
        """Check if audio quality is poor enough to benefit from AI enhancement."""
        return self.quality_score < 0.5 or self.snr_db < 20

    @property
    def is_high_quality(self) -> bool:
        """Check if audio is already high quality (good or better)."""
        return self.quality_score >= 0.7

    @property
    def is_excellent_quality(self) -> bool:
        """Check if audio is excellent quality and needs minimal processing."""
        return self.quality_score >= 0.8

    @property
    def quality_level(self) -> str:
        """Get human-readable quality level."""
        if self.quality_score < 0.3:
            return "Poor"
        elif self.quality_score < 0.6:
            return "Medium"
        elif self.quality_score < 0.8:
            return "Good"
        else:
            return "Excellent"

    def improvement_from(self, other: "QualityMetrics") -> float:
        """Calculate quality improvement percentage from another metrics instance.

        Args:
            other: The previous/input quality metrics.

        Returns:
            Improvement percentage (e.g., 0.67 for 67% improvement).
        """
        if other.quality_score == 0:
            return 0.0
        return (self.quality_score - other.quality_score) / other.quality_score
