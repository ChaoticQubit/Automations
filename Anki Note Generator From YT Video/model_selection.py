import os
from typing import Callable, Dict, List, Optional, Tuple

from schemas import TopicsResponse, FlashcardsResponse


def _safe_list_groq_models() -> List[str]:
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_TOKEN")
        if not api_key:
            raise RuntimeError("no groq key")
        client = Groq(api_key=api_key)
        models = getattr(getattr(client, "models", None), "list", None)
        if callable(models):
            resp = models()
            names: List[str] = []
            for m in getattr(resp, "data", []) or []:
                name = getattr(m, "id", None) or getattr(m, "name", None)
                if isinstance(name, str):
                    names.append(name)
            if names:
                return sorted(names)
    except Exception:
        pass
    return ["openai/gpt-oss-120b"]


def _safe_list_gemini_models() -> List[str]:
    try:
        from google import genai

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("no gemini key")
        client = genai.Client(api_key=api_key)
        names: List[str] = []
        for model in client.models.list():
            for action in model.supported_actions:
                if action == "generateContent":
                    names.append(model.name)
                    break
        return sorted(list(dict.fromkeys(names)))
    except Exception:
        pass
    return ["gemini-1.5-pro", "gemini-1.5-flash"]


def list_models() -> Dict[str, List[str]]:
    return {
        "groq": _safe_list_groq_models(),
        "gemini": _safe_list_gemini_models(),
    }


def get_generator(provider: str) -> Callable[[str, Optional[str]], Tuple[TopicsResponse, FlashcardsResponse]]:
    normalized = (provider or "").strip().lower()
    if normalized == "gemini":
        from gemini_client import generate_topics_and_flashcards as gen

        return gen
    # default to groq
    from groq_client import generate_topics_and_flashcards as gen

    return gen


