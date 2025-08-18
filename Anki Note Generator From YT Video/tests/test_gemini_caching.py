import sys
import asyncio
from types import SimpleNamespace
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _DummyGenerateContentConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeCaches:
    def __init__(self):
        self.last_create_kwargs = None

    def create(self, **kwargs):
        self.last_create_kwargs = kwargs
        # Return an object carrying a name attribute like the real API
        return SimpleNamespace(name="projects/demo/locations/us/cachedContents/123")


class _FakeModels:
    def __init__(self):
        self.calls = []

    def generate_content(self, *, model, contents, config=None, cached_content=None):
        # record the arguments for assertions
        self.calls.append({
            "model": model,
            "contents": contents,
            "cached_content": cached_content,
        })

        # Create a minimal response object with .text like google.genai returns
        text = ""
        # Heuristic: if prompt mentions "Topics JSON:", return flashcards JSON; otherwise topics JSON
        if isinstance(contents, str):
            prompt_text = contents
        elif isinstance(contents, list) and contents and isinstance(contents[0], str):
            prompt_text = "\n".join(contents)
        else:
            prompt_text = str(contents)

        if "Topics JSON:" in prompt_text:
            text = '{"decks":[{"topic":"A","subtopic":"B","cards":[{"type":"qa","question":"q","answer":"a"}]}]}'
        else:
            text = '{"topics":[{"title":"A","subtopics":[{"title":"B","summary":"s","key_points":["k1","k2"]}]}]}'

        return SimpleNamespace(text=text)


class _FakeGenAIClient:
    def __init__(self, *_, **__):
        self.caches = _FakeCaches()
        self.models = _FakeModels()


def test_gemini_uses_context_cache_and_omits_transcript(monkeypatch):
    import gemini_client as gc

    # Monkeypatch the google.genai client and types
    monkeypatch.setattr(gc, "genai", SimpleNamespace(Client=_FakeGenAIClient))
    monkeypatch.setattr(gc, "types", SimpleNamespace(GenerateContentConfig=_DummyGenerateContentConfig))

    # Ensure environment is set so code path selects gemini and model name
    transcript = "THIS IS THE TRANSCRIPT. DO NOT ECHO THIS INTO PROMPTS."

    topics, flashcards = asyncio.run(gc.generate_topics_and_flashcards(transcript, model="models/test-model"))

    # Validate parsed structures
    assert topics.topics and topics.topics[0].title == "A"
    assert flashcards.decks and flashcards.decks[0].topic == "A"

    # Access the fake client used inside generate_topics_and_flashcards
    # We can't access it directly, but our fakes record their last call
    client = gc._LAST_FAKE_CLIENT  # type: ignore[attr-defined]

    # 1) Cache was created with 5 minute TTL and contains the transcript
    assert client.caches.last_create_kwargs is not None
    create_kwargs = client.caches.last_create_kwargs
    assert create_kwargs.get("model") == "models/test-model"
    # ttl could be provided as string or seconds field; accept either
    assert (create_kwargs.get("ttl") == "300s") or (create_kwargs.get("ttlSeconds") == 300)

    # Ensure transcript is present in cached contents, not in subsequent prompts
    contents_payload = create_kwargs.get("contents") or []
    flat_text = str(contents_payload)
    assert "THIS IS THE TRANSCRIPT" in flat_text

    # 2) Subsequent generate calls must reference cached_content and must not include transcript
    calls = client.models.calls
    assert len(calls) >= 2
    for call in calls[:2]:
        assert call.get("cached_content") == "projects/demo/locations/us/cachedContents/123"
        assert "THIS IS THE TRANSCRIPT" not in (call.get("contents") or "")


