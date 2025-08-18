import asyncio
import json
import os
import re
from typing import Tuple

from google import genai
from google.genai import types

from prompts import _topics_prompt, _flashcards_prompt
from schemas import TopicsResponse, FlashcardsResponse


def _strip_to_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from LLM text.

    Never raises; returns an empty dict on failure.
    """
    if not isinstance(text, str):
        return {}

    text = text.strip()
    if not text:
        return {}

    # Prefer fenced code blocks first
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        if fenced:
            try:
                obj = json.loads(fenced)
                return obj if isinstance(obj, dict) else {"data": obj}
            except Exception:
                # try json5 as a fallback for fenced content
                try:
                    import json5  # type: ignore

                    parsed = json5.loads(fenced)
                    obj = json.loads(json.dumps(parsed))
                    return obj if isinstance(obj, dict) else {"data": obj}
                except Exception:
                    pass

    # Try direct JSON first
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {"data": obj}
    except Exception:
        pass

    # Extract largest {...} or [...] segment and try that
    brace_start, brace_end = text.find("{"), text.rfind("}")
    bracket_start, bracket_end = text.find("["), text.rfind("]")

    candidate = None
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = text[brace_start : brace_end + 1]
    elif bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
        candidate = text[bracket_start : bracket_end + 1]

    if candidate:
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else {"data": obj}
        except Exception:
            # try json5 on candidate
            try:
                import json5  # type: ignore

                parsed = json5.loads(candidate)
                obj = json.loads(json.dumps(parsed))
                return obj if isinstance(obj, dict) else {"data": obj}
            except Exception:
                pass

    # json5 last resort on full text
    try:
        import json5  # type: ignore

        parsed = json5.loads(text)
        obj = json.loads(json.dumps(parsed))
        return obj if isinstance(obj, dict) else {"data": obj}
    except Exception:
        return {}


_LAST_FAKE_CLIENT = None  # testing hook to inspect the instantiated client


async def generate_topics_and_flashcards(transcript: str, model: str | None = None) -> Tuple[TopicsResponse, FlashcardsResponse]:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is not set")
    client = genai.Client(api_key=api_key)
    # Expose the client for tests that monkeypatch and need to inspect calls
    global _LAST_FAKE_CLIENT
    _LAST_FAKE_CLIENT = client

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    # Create a 5-minute explicit context cache for the transcript
    cached = client.caches.create(
        model=model_name,
        config=types.CreateCachedContentConfig(
            contents=[transcript],
            system_instruction="You are an expert at analyzing transcripts and creating Anki flashcards.",
            ttl="300s",
        )
    )

    def _generate(prompt: str, max_tokens: int, response_schema) -> str:
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0,
            top_p=0.95,
            top_k=40,
            response_mime_type="application/json",
            response_schema=response_schema,
            cached_content=getattr(cached, "name", None),
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        text = getattr(response, "text", None)
        if not text and hasattr(response, "candidates") and response.candidates:
            for cand in response.candidates:
                parts = []
                try:
                    content = getattr(cand, "content", None)
                    for part in getattr(content, "parts", []) or []:
                        val = getattr(part, "text", None)
                        if isinstance(val, str):
                            parts.append(val)
                except Exception:
                    continue
            text = "\n".join(parts)
        return text or ""

    # Build prompts that rely on cached transcript rather than embedding it again
    # 1) Topics prompt (do not include transcript text)
    cached_topics_prompt = (
        "You are an assistant that returns strict JSON only. "
        "Extract a list of high-quality learning topics with subtopics from the cached transcript. "
        "Do not create topics for the course description, instructor, or any other non-learning content. Only create topics for the learning content that is important to learn. "
        "Return ONLY valid JSON matching this schema: {\n  \"topics\": [ { \n    \"title\": string,\n    \"subtopics\": [ { \n      \"title\": string, \n      \"summary\": string, \n      \"key_points\": string[] \n    } ] \n  } ] \n}\n"
    )

    loop = asyncio.get_event_loop()
    topics_text = await loop.run_in_executor(None, lambda: _generate(cached_topics_prompt, 65_535, response_schema=TopicsResponse))
    topics_json = _strip_to_json(topics_text)
    topics = TopicsResponse.model_validate(topics_json)

    # 2) Flashcards prompt: include topics JSON but not the transcript (still in cache)
    cached_flashcards_prompt = (
        "You are an assistant that returns strict JSON. "
        "Create Anki flashcards for the given topics and subtopics. Create as many flashcards as possible for each topic and subtopic. Limit the number of flashcards to 50 for each topic."
        "Do not create flashcards for the course description, instructor, or any other non-learning content. Only create flashcards for the learning content that is important to learn."
        "Create some flashcards for the examples, exercises, questions, etc. that is not the main learning content. These are important to learn and review, but not the main learning content."
        "Card types allowed: qa, single_choice, multiple_choice, matching. "
        "For choice questions, include options and the correct index(es). "
        "Return ONLY valid JSON matching this schema: "
        "{\n  \"decks\": [\n    {\n      \"topic\": string,\n      \"subtopic\": string?,\n      \"cards\": [\n        { \n          \"type\": \"qa\", \n          \"question\": string, \n          \"answer\": string, \n          \"explanation\": string? \n        } | { \n          \"type\": \"single_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_option\": number, \n          \"explanation\": string? \n        } | { \n          \"type\": \"multiple_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_options\": number[], \n          \"explanation\": string? \n        } | { \n          \"type\": \"matching\", \n          \"question\": string?, \n          \"pairs\": [ { \"left\": string, \"right\": string } ] \n        }\n      ]\n    }\n  ]\n}"
        f"\nTopics JSON:\n{json.dumps(topics_json, ensure_ascii=False)}"
    )

    flash_text = await loop.run_in_executor(None, lambda: _generate(cached_flashcards_prompt, 65_535, response_schema=FlashcardsResponse))
    flash_json = _strip_to_json(flash_text)
    flashcards = FlashcardsResponse.model_validate(flash_json)

    return topics, flashcards


