"""Tests for config/llm_models/loader.py."""

from __future__ import annotations

import pytest

from config.llm_models.loader import LLMModelConfig, load_model_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _yaml_content(
    model: str = "claude-opus-4-5",
    max_tokens: int = 1024,
    effort: str | None = None,
) -> str:
    base = f"model: {model}\nmax_tokens: {max_tokens}\n"
    if effort is not None:
        base += f"effort: {effort}\n"
    return base


# ---------------------------------------------------------------------------
# LLMModelConfig dataclass
# ---------------------------------------------------------------------------


def test_llm_model_config_is_immutable():
    cfg = LLMModelConfig(model="claude-opus-4-5", max_tokens=1024)
    with pytest.raises((AttributeError, TypeError)):
        cfg.model = "other"  # type: ignore[misc]


def test_llm_model_config_fields():
    cfg = LLMModelConfig(model="claude-opus-4-5", max_tokens=2048)
    assert cfg.model == "claude-opus-4-5"
    assert cfg.max_tokens == 2048
    assert cfg.effort == "high"


def test_llm_model_config_effort_explicit():
    cfg = LLMModelConfig(model="claude-opus-4-5", max_tokens=1024, effort="low")
    assert cfg.effort == "low"


# ---------------------------------------------------------------------------
# load_model_config — happy path
# ---------------------------------------------------------------------------


def test_load_model_config_reads_yaml(tmp_path, monkeypatch):
    yaml_file = tmp_path / "support_agent.yaml"
    yaml_file.write_text("model: claude-opus-4-5\nmax_tokens: 1024\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    cfg = load_model_config("support_agent")

    assert cfg.model == "claude-opus-4-5"
    assert cfg.max_tokens == 1024
    assert cfg.effort == "high"


def test_load_model_config_reads_effort_from_yaml(tmp_path, monkeypatch):
    yaml_file = tmp_path / "support_agent.yaml"
    yaml_file.write_text(
        "model: claude-opus-4-5\nmax_tokens: 1024\neffort: low\n", encoding="utf-8"
    )

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    cfg = load_model_config("support_agent")

    assert cfg.effort == "low"


def test_load_model_config_effort_defaults_to_high_when_absent(tmp_path, monkeypatch):
    yaml_file = tmp_path / "support_agent.yaml"
    yaml_file.write_text("model: claude-opus-4-5\nmax_tokens: 1024\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    cfg = load_model_config("support_agent")

    assert cfg.effort == "high"


def test_load_model_config_returns_llm_model_config_instance(tmp_path, monkeypatch):
    yaml_file = tmp_path / "my_agent.yaml"
    yaml_file.write_text("model: claude-haiku-3-5\nmax_tokens: 512\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    cfg = load_model_config("my_agent")

    assert isinstance(cfg, LLMModelConfig)
    assert cfg.model == "claude-haiku-3-5"
    assert cfg.max_tokens == 512


# ---------------------------------------------------------------------------
# load_model_config — error cases
# ---------------------------------------------------------------------------


def test_load_model_config_raises_file_not_found(tmp_path, monkeypatch):
    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="nonexistent"):
        load_model_config("nonexistent")


def test_load_model_config_raises_on_missing_model_field(tmp_path, monkeypatch):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("max_tokens: 1024\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(ValueError, match="model"):
        load_model_config("bad")


def test_load_model_config_raises_on_missing_max_tokens_field(tmp_path, monkeypatch):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("model: claude-opus-4-5\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(ValueError, match="max_tokens"):
        load_model_config("bad")


def test_load_model_config_raises_on_empty_model_string(tmp_path, monkeypatch):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("model: ''\nmax_tokens: 1024\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(ValueError, match="model"):
        load_model_config("bad")


def test_load_model_config_raises_on_non_positive_max_tokens(tmp_path, monkeypatch):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("model: claude-opus-4-5\nmax_tokens: 0\n", encoding="utf-8")

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(ValueError, match="max_tokens"):
        load_model_config("bad")


def test_load_model_config_raises_on_invalid_effort(tmp_path, monkeypatch):
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text(
        "model: claude-opus-4-5\nmax_tokens: 1024\neffort: turbo\n", encoding="utf-8"
    )

    import config.llm_models.loader as loader_module

    monkeypatch.setattr(loader_module, "_CONFIG_DIR", tmp_path)

    with pytest.raises(ValueError, match="effort"):
        load_model_config("bad")


# ---------------------------------------------------------------------------
# __init__.py re-exports
# ---------------------------------------------------------------------------


def test_public_api_exports():
    from config.llm_models import LLMModelConfig as C
    from config.llm_models import load_model_config as f

    assert C is LLMModelConfig
    assert callable(f)
