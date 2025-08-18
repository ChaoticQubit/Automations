import asyncio
import json
import os
import re
from typing import Tuple

from groq import Groq

from prompts import _topics_prompt, _flashcards_prompt
from schemas import TopicsResponse, FlashcardsResponse


def _strip_to_json(text: str) -> dict:
    text = text.strip()

    # If response is fenced as a code block, extract the fenced content
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct strict JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting the largest braced object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fall back to JSON5 for non-strict JSON (single quotes, trailing commas, etc.)
    try:
        import json5  # type: ignore

        parsed = json5.loads(text)
        # Re-serialize to strict JSON and load again to ensure standard structure
        return json.loads(json.dumps(parsed))
    except Exception as exc:
        # Re-try with candidate slice in JSON5
        if start != -1 and end != -1 and end > start:
            try:
                import json5  # type: ignore

                parsed = json5.loads(candidate)
                return json.loads(json.dumps(parsed))
            except Exception:
                pass
        # Bubble up with context for troubleshooting
        raise json.JSONDecodeError("Failed to parse model JSON output", text, 0) from exc


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_TOKEN")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


async def generate_topics_and_flashcards(transcript: str, model: str | None = None) -> Tuple[TopicsResponse, FlashcardsResponse]:
    client = _get_groq_client()

    def _chat_completion(prompt: str, max_tokens: int) -> str:
        resp = client.chat.completions.create(
            model=(model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    loop = asyncio.get_event_loop()
    topics_text = await loop.run_in_executor(
        None, lambda: _chat_completion(_topics_prompt(transcript), 65_535)
    )
    topics_json = _strip_to_json(topics_text)
    topics = TopicsResponse.model_validate(topics_json)

    flash_text = await loop.run_in_executor(
        None,
        lambda: _chat_completion(_flashcards_prompt(topics_json, transcript), 65_535),
    )
    flash_json = _strip_to_json(flash_text)
    flashcards = FlashcardsResponse.model_validate(flash_json)

    return topics, flashcards


