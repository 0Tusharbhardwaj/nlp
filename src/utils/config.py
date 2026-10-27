"""Configuration loader and environment management for SecureCode AI."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file.
    
    Args:
        config_path: Path to configuration YAML. Defaults to configs/base.yaml
                    relative to the project root.
                    
    Returns:
        Dict containing configuration parameters.
        
    Raises:
        FileNotFoundError: If the config file cannot be found.
    """
    if config_path is None:
        root = get_project_root()
        config_path = str(root / "configs" / "base.yaml")
    
    path = Path(config_path)
    if not path.is_absolute():
        path = get_project_root() / path
        
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")
        
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    return config or {}


def set_seed(seed: int = 42) -> None:
    """Set random seed across Python, NumPy, and PyTorch for strict reproducibility."""
    import random
    import numpy as np

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
