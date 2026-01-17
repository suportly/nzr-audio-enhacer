"""AI model management service for DeepFilterNet."""

import os
from pathlib import Path
from typing import Any, Optional

# DeepFilterNet imports are optional - gracefully handle if not installed
try:
    from df.enhance import enhance, init_df
    DEEPFILTERNET_AVAILABLE = True
except ImportError:
    DEEPFILTERNET_AVAILABLE = False
    init_df = None
    enhance = None


# Global model cache
_model_cache: dict[str, Any] = {}


def get_model_path() -> Path:
    """Get the path where AI models are stored.

    Checks environment variable ENHANCE_AUDIO_MODEL_PATH first,
    then falls back to default cache directory.

    Returns:
        Path to model storage directory.
    """
    env_path = os.environ.get("ENHANCE_AUDIO_MODEL_PATH")
    if env_path:
        return Path(env_path)

    # Default: ~/.cache/enhance-audio/models
    cache_dir = Path.home() / ".cache" / "enhance-audio" / "models"
    return cache_dir


def is_model_available() -> bool:
    """Check if DeepFilterNet model is available.

    Returns:
        True if DeepFilterNet is installed and model can be loaded.
    """
    if not DEEPFILTERNET_AVAILABLE:
        return False

    try:
        # Try to initialize to verify model availability
        load_deepfilternet()
        return True
    except Exception:
        return False


def load_deepfilternet() -> tuple[Any, Any, Any]:
    """Load the DeepFilterNet model.

    Returns:
        Tuple of (model, df_state, sr) from DeepFilterNet.

    Raises:
        RuntimeError: If DeepFilterNet is not installed or model cannot be loaded.
    """
    if not DEEPFILTERNET_AVAILABLE:
        raise RuntimeError(
            "DeepFilterNet is not installed. Install with: pip install deepfilternet"
        )

    # Check cache first
    if "deepfilternet" in _model_cache:
        return _model_cache["deepfilternet"]

    try:
        # Initialize DeepFilterNet with default model
        model, df_state, sr = init_df()
        _model_cache["deepfilternet"] = (model, df_state, sr)
        return model, df_state, sr
    except Exception as e:
        raise RuntimeError(f"Failed to load DeepFilterNet model: {e}")


def unload_models() -> None:
    """Unload all cached models to free memory."""
    global _model_cache
    _model_cache.clear()


def download_models(force: bool = False) -> bool:
    """Download AI models if not already present.

    DeepFilterNet downloads models automatically on first use,
    but this function can be used to pre-download.

    Args:
        force: If True, re-download even if models exist.

    Returns:
        True if download was successful or models already exist.
    """
    if not DEEPFILTERNET_AVAILABLE:
        return False

    try:
        # Simply initialize the model - it auto-downloads if needed
        load_deepfilternet()
        return True
    except Exception:
        return False
