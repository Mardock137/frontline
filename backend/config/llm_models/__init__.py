"""Public API for the llm_models config module."""

from config.llm_models.loader import LLMModelConfig, load_model_config

__all__ = ["LLMModelConfig", "load_model_config"]
