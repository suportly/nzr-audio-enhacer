"""Progress reporting utility for audio processing."""

import time
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from tqdm import tqdm


class ProgressReporter:
    """Reports progress during audio enhancement.

    Provides methods to track stage progress and display
    visual feedback using tqdm progress bars.
    """

    def __init__(
        self,
        verbose: bool = False,
        quiet: bool = False,
        total_stages: int = 5,
    ):
        """Initialize the progress reporter.

        Args:
            verbose: If True, show detailed progress information.
            quiet: If True, suppress all progress output.
            total_stages: Total number of processing stages.
        """
        self.verbose = verbose
        self.quiet = quiet
        self.total_stages = total_stages
        self.current_stage = 0
        self.stage_name = ""
        self.stage_start_time = 0.0
        self.overall_start_time = time.time()
        self._pbar: Optional[tqdm] = None
        self._stage_pbar: Optional[tqdm] = None

    def start_stage(self, name: str, total: int = 100) -> None:
        """Start a new processing stage.

        Args:
            name: Name of the stage (e.g., "noise_reduction").
            total: Total units of work for this stage.
        """
        if self.quiet:
            return

        self.current_stage += 1
        self.stage_name = name
        self.stage_start_time = time.time()

        # Close previous stage progress bar if open
        if self._stage_pbar is not None:
            self._stage_pbar.close()
            self._stage_pbar = None

        # Create stage progress bar
        desc = f"Stage {self.current_stage}/{self.total_stages}: {name}"
        self._stage_pbar = tqdm(
            total=total,
            desc=desc,
            unit="%",
            leave=False,
            ncols=80,
            bar_format="{desc}: {bar} {percentage:3.0f}%",
        )

    def update(self, amount: int = 1) -> None:
        """Update progress within current stage.

        Args:
            amount: Amount of progress to add.
        """
        if self.quiet or self._stage_pbar is None:
            return

        self._stage_pbar.update(amount)

    def set_progress(self, percentage: float) -> None:
        """Set absolute progress percentage for current stage.

        Args:
            percentage: Progress percentage (0 to 100).
        """
        if self.quiet or self._stage_pbar is None:
            return

        current = self._stage_pbar.n
        target = int(percentage)
        if target > current:
            self._stage_pbar.update(target - current)

    def complete_stage(self) -> None:
        """Mark current stage as complete."""
        if self.quiet:
            return

        if self._stage_pbar is not None:
            # Fill to 100% if not already
            remaining = self._stage_pbar.total - self._stage_pbar.n
            if remaining > 0:
                self._stage_pbar.update(remaining)
            self._stage_pbar.close()
            self._stage_pbar = None

        if self.verbose:
            elapsed = time.time() - self.stage_start_time
            print(f"  {self.stage_name}: completed in {elapsed:.2f}s")

    def skip_stage(self, name: str) -> None:
        """Mark a stage as skipped.

        Args:
            name: Name of the skipped stage.
        """
        if self.quiet:
            return

        self.current_stage += 1
        if self.verbose:
            print(f"  {name}: skipped")

    def estimate_remaining_time(self) -> float:
        """Estimate remaining processing time.

        Returns:
            Estimated remaining time in seconds.
        """
        if self.current_stage == 0:
            return 0.0

        elapsed = time.time() - self.overall_start_time
        avg_per_stage = elapsed / self.current_stage
        remaining_stages = self.total_stages - self.current_stage

        return avg_per_stage * remaining_stages

    def get_eta_string(self) -> str:
        """Get human-readable ETA string.

        Returns:
            ETA string like "~2m 30s" or "~45s".
        """
        remaining = self.estimate_remaining_time()
        if remaining <= 0:
            return "almost done"

        minutes = int(remaining // 60)
        seconds = int(remaining % 60)

        if minutes > 0:
            return f"~{minutes}m {seconds}s"
        else:
            return f"~{seconds}s"

    def close(self) -> None:
        """Clean up progress bars."""
        if self._stage_pbar is not None:
            self._stage_pbar.close()
            self._stage_pbar = None
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None


@contextmanager
def progress_stage(
    reporter: Optional[ProgressReporter],
    name: str,
    total: int = 100,
) -> Iterator[Callable[[int], None]]:
    """Context manager for a processing stage.

    Args:
        reporter: ProgressReporter instance (can be None).
        name: Stage name.
        total: Total work units.

    Yields:
        Update function to call with progress increments.

    Example:
        with progress_stage(reporter, "noise_reduction") as update:
            for chunk in chunks:
                process(chunk)
                update(10)
    """
    if reporter is None:
        yield lambda x: None
        return

    reporter.start_stage(name, total)
    try:
        yield reporter.update
    finally:
        reporter.complete_stage()


def create_reporter(verbose: bool = False, quiet: bool = False) -> Optional[ProgressReporter]:
    """Create a progress reporter or None if quiet.

    Args:
        verbose: If True, show detailed progress.
        quiet: If True, return None (no progress output).

    Returns:
        ProgressReporter instance or None.
    """
    if quiet:
        return None
    return ProgressReporter(verbose=verbose, quiet=False)
