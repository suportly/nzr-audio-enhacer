"""Custom exception types for the music enhancer."""


class EnhancerError(Exception):
    """Base exception for all enhancer errors."""

    exit_code: int = 4  # Default: processing failed

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidFormatError(EnhancerError):
    """Raised when input file is not a valid .wav file."""

    exit_code = 3

    def __init__(self, path: str, details: str = ""):
        message = f"Input file is not a valid WAV file: {path}"
        if details:
            message += f" ({details})"
        super().__init__(message)


class AudioFileNotFoundError(EnhancerError):
    """Raised when input file path doesn't exist."""

    exit_code = 2

    def __init__(self, path: str):
        super().__init__(f"Input file not found: {path}")


class FileCorruptedError(EnhancerError):
    """Raised when file exists but cannot be read."""

    exit_code = 3

    def __init__(self, path: str, details: str = ""):
        message = f"Input file appears to be corrupted: {path}"
        if details:
            message += f" ({details})"
        super().__init__(message)


class UnsupportedChannelsError(EnhancerError):
    """Raised when audio has more than 2 channels."""

    exit_code = 3

    def __init__(self, channels: int):
        super().__init__(
            f"Only mono and stereo audio supported (got {channels} channels)"
        )


class InsufficientSpaceError(EnhancerError):
    """Raised when there's not enough disk space for output file."""

    exit_code = 5

    def __init__(self, path: str):
        super().__init__(f"Insufficient disk space for output file: {path}")


class ProcessingFailedError(EnhancerError):
    """Raised when enhancement processing fails."""

    exit_code = 4

    def __init__(self, stage: str, details: str = ""):
        message = f"Processing failed during {stage}"
        if details:
            message += f": {details}"
        super().__init__(message)


class ModelUnavailableError(EnhancerError):
    """Raised when AI model cannot be loaded."""

    exit_code = 4

    def __init__(self, model_name: str = "DeepFilterNet"):
        super().__init__(
            f"AI enhancement unavailable ({model_name} model not found), "
            "using standard processing"
        )


class OutputWriteError(EnhancerError):
    """Raised when output file cannot be written."""

    exit_code = 5

    def __init__(self, path: str, details: str = ""):
        message = f"Failed to write output file: {path}"
        if details:
            message += f" ({details})"
        super().__init__(message)
