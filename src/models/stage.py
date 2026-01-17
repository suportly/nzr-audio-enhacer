"""ProcessingStage data class for tracking individual enhancement steps."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessingStage:
    """Individual step in the enhancement pipeline.

    Attributes:
        name: Stage identifier (e.g., "noise_reduction", "spectral", "dynamics").
        enabled: Whether the stage was executed.
        method: Technique used (e.g., "deepfilternet", "spectral_gating").
        parameters: Parameters applied during this stage.
        duration_seconds: Time taken for this stage.
    """

    name: str
    enabled: bool
    method: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0

    @classmethod
    def skipped(cls, name: str) -> "ProcessingStage":
        """Create a skipped stage record."""
        return cls(name=name, enabled=False, method="skipped")

    @classmethod
    def completed(
        cls,
        name: str,
        method: str,
        duration: float,
        parameters: dict[str, Any] | None = None,
    ) -> "ProcessingStage":
        """Create a completed stage record.

        Args:
            name: Stage name.
            method: Method used.
            duration: Time taken in seconds.
            parameters: Parameters used.

        Returns:
            ProcessingStage instance.
        """
        return cls(
            name=name,
            enabled=True,
            method=method,
            parameters=parameters or {},
            duration_seconds=duration,
        )
