# ruff: noqa
from pathlib import Path

import types


def test_list_models_includes_groq_and_gemini():
    from model_selection import list_models

    all_models = list_models()
    assert "groq" in all_models
    assert "gemini" in all_models
    assert isinstance(all_models["groq"], list) and len(all_models["groq"]) >= 1
    assert isinstance(all_models["gemini"], list) and len(all_models["gemini"]) >= 1


def test_get_generator_returns_callable_for_each_provider(tmp_path: Path):
    from model_selection import get_generator

    groq_gen = get_generator("groq")
    gemini_gen = get_generator("gemini")

    assert isinstance(groq_gen, types.FunctionType)
    assert isinstance(gemini_gen, types.FunctionType)


