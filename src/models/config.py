"""EnhancementConfig data class for enhancement pipeline configuration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityLevel(Enum):
    """Processing intensity levels."""

    AUTO = "auto"
    MINIMAL = "minimal"
    LIGHT = "light"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


@dataclass
class EnhancementConfig:
    """Configuration parameters for the enhancement pipeline.

    Attributes:
        noise_reduction_strength: Intensity of noise reduction (0.0 to 1.0).
        eq_enabled: Whether to apply equalization.
        dynamics_enabled: Whether to apply dynamic range processing.
        ai_enhancement_enabled: Whether to use AI models if needed.
        preserve_dynamics: Whether to avoid over-compression.
        target_loudness_lufs: Target integrated loudness in LUFS.
        quality_level: Overall processing intensity level.
    """

    noise_reduction_strength: float = 0.5
    eq_enabled: bool = True
    dynamics_enabled: bool = True
    ai_enhancement_enabled: bool = True
    preserve_dynamics: bool = True
    target_loudness_lufs: float = -14.0
    quality_level: QualityLevel = QualityLevel.AUTO

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.noise_reduction_strength <= 1.0:
            raise ValueError("noise_reduction_strength must be between 0.0 and 1.0")
        if not -60.0 <= self.target_loudness_lufs <= 0.0:
            raise ValueError("target_loudness_lufs must be between -60.0 and 0.0")

    @classmethod
    def minimal(cls) -> "EnhancementConfig":
        """Create a minimal processing configuration for excellent quality inputs.

        This configuration preserves the original quality by only applying
        very subtle noise reduction without EQ or dynamics changes.
        """
        return cls(
            noise_reduction_strength=0.1,
            eq_enabled=False,
            dynamics_enabled=False,
            ai_enhancement_enabled=False,
            preserve_dynamics=True,
            quality_level=QualityLevel.MINIMAL,
        )

    @classmethod
    def light(cls) -> "EnhancementConfig":
        """Create a light processing configuration for high-quality inputs."""
        return cls(
            noise_reduction_strength=0.2,
            eq_enabled=True,
            dynamics_enabled=True,
            ai_enhancement_enabled=False,
            preserve_dynamics=True,
            quality_level=QualityLevel.LIGHT,
        )

    @classmethod
    def standard(cls) -> "EnhancementConfig":
        """Create a standard processing configuration for average quality inputs."""
        return cls(
            noise_reduction_strength=0.5,
            eq_enabled=True,
            dynamics_enabled=True,
            ai_enhancement_enabled=True,
            preserve_dynamics=True,
            quality_level=QualityLevel.STANDARD,
        )

    @classmethod
    def aggressive(cls) -> "EnhancementConfig":
        """Create an aggressive processing configuration for poor quality inputs."""
        return cls(
            noise_reduction_strength=0.8,
            eq_enabled=True,
            dynamics_enabled=True,
            ai_enhancement_enabled=True,
            preserve_dynamics=False,
            quality_level=QualityLevel.AGGRESSIVE,
        )
