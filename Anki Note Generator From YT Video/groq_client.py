import asyncio
import json
import os
from typing import Tuple

from groq import Groq

from schemas import TopicsResponse, FlashcardsResponse


def _strip_to_json(text: str) -> dict:
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to extract the largest JSON object substring
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
        raise


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_TOKEN")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def _topics_prompt(transcript: str) -> str:
    return (
        "You are an assistant that returns strict JSON. "
        "Analyze the transcript and extract topics with subtopics. "
        "If the content is a lecture series, subtopics should be lectures. "
        "Otherwise, choose appropriate subtopic grouping. "
        "Return ONLY valid JSON matching this schema: "
        "{\n  \"topics\": [\n    {\n      \"title\": string,\n      \"subtopics\": [ { \n        \"title\": string, \n        \"summary\": string?, \n        \"key_points\": string[]? \n      } ]\n    }\n  ]\n}"
        "\nTranscript:\n" + transcript
    )


def _flashcards_prompt(topics_json: dict, transcript: str) -> str:
    return (
        "You are an assistant that returns strict JSON. "
        "Create Anki flashcards for the given topics and subtopics. "
        "Card types allowed: qa, single_choice, multiple_choice, matching. "
        "For choice questions, include options and the correct index(es). "
        "Return ONLY valid JSON matching this schema: "
        "{\n  \"decks\": [\n    {\n      \"topic\": string,\n      \"subtopic\": string?,\n      \"cards\": [\n        { \n          \"type\": \"qa\", \n          \"question\": string, \n          \"answer\": string, \n          \"explanation\": string? \n        } | { \n          \"type\": \"single_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_option\": number, \n          \"explanation\": string? \n        } | { \n          \"type\": \"multiple_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_options\": number[], \n          \"explanation\": string? \n        } | { \n          \"type\": \"matching\", \n          \"question\": string?, \n          \"pairs\": [ { \"left\": string, \"right\": string } ] \n        }\n      ]\n    }\n  ]\n}"
        f"\nTopics JSON:\n{json.dumps(topics_json, ensure_ascii=False)}"
        f"\nTranscript (for context; do not copy verbatim):\n{transcript[:8000]}"
    )


async def generate_topics_and_flashcards(transcript: str) -> Tuple[TopicsResponse, FlashcardsResponse]:
    client = _get_groq_client()

    def _chat_completion(prompt: str, max_tokens: int) -> str:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    loop = asyncio.get_event_loop()
    topics_text = await loop.run_in_executor(
        None, lambda: _chat_completion(_topics_prompt(transcript), 1500)
    )
    topics_json = _strip_to_json(topics_text)
    topics = TopicsResponse.model_validate(topics_json)

    flash_text = await loop.run_in_executor(
        None,
        lambda: _chat_completion(_flashcards_prompt(topics_json, transcript), 3000),
    )
    flash_json = _strip_to_json(flash_text)
    flashcards = FlashcardsResponse.model_validate(flash_json)

    return topics, flashcards


