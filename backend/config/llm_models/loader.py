"""Loader for LLM model configuration YAML files.

Each agent has its own ``<name>.yaml`` file inside ``config/llm_models/``.
The loader reads the file, validates that all required fields are present and
returns an immutable ``LLMModelConfig`` dataclass.

Usage::

    from config.llm_models.loader import load_model_config

    cfg = load_model_config("support_agent")
    print(cfg.model)       # "claude-opus-4-5"
    print(cfg.max_tokens)  # 1024
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent

_REQUIRED_FIELDS = ("model", "max_tokens")

_VALID_EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max"}
_DEFAULT_EFFORT = "high"


@dataclass(frozen=True)
class LLMModelConfig:
    """Immutable LLM model configuration loaded from a YAML file.

    Attributes:
        model: The model identifier string (e.g. ``"claude-opus-4-5"``).
        max_tokens: Maximum number of tokens the model may generate.
        effort: How many tokens Claude spends on the response, covering text,
            tool calls and any thinking (it does not require thinking to be
            enabled). One of ``low``, ``medium``, ``high``, ``xhigh``, ``max``.
            Defaults to ``"high"`` when not specified in the YAML file.
    """

    model: str
    max_tokens: int
    effort: str = _DEFAULT_EFFORT


def load_model_config(name: str) -> LLMModelConfig:
    """Load and validate a model config from ``config/llm_models/{name}.yaml``.

    Args:
        name: Name of the config file without extension (e.g. ``"support_agent"``).

    Returns:
        A validated, immutable ``LLMModelConfig``.

    Raises:
        FileNotFoundError: If ``{name}.yaml`` does not exist in the config dir.
        ValueError: If a required field is missing or has an invalid type.
    """
    config_path = _CONFIG_DIR / f"{name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"LLM model config not found: '{config_path}'. "
            f"Create 'backend/config/llm_models/{name}.yaml'."
        )

    with config_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(
                f"Missing required field '{field}' in '{config_path.name}'."
            )

    model = data["model"]
    max_tokens = data["max_tokens"]
    effort = data.get("effort", _DEFAULT_EFFORT)

    if not isinstance(model, str) or not model.strip():
        raise ValueError(
            f"Field 'model' in '{config_path.name}' must be a non-empty string."
        )
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ValueError(
            f"Field 'max_tokens' in '{config_path.name}' must be a positive integer."
        )
    if effort not in _VALID_EFFORT_VALUES:
        raise ValueError(
            f"Field 'effort' in '{config_path.name}' must be one of "
            f"{sorted(_VALID_EFFORT_VALUES)}, got '{effort}'."
        )

    return LLMModelConfig(model=model, max_tokens=max_tokens, effort=effort)
