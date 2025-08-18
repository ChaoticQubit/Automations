import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_strip_to_json_empty_returns_empty_dict():
    from gemini_client import _strip_to_json

    assert _strip_to_json("") == {}
    assert _strip_to_json("   \n\n   ") == {}


def test_strip_to_json_parses_code_fence():
    from gemini_client import _strip_to_json

    text = """
Here is the result:
```json
{ "topics": [] }
```
"""
    assert _strip_to_json(text) == {"topics": []}


def test_strip_to_json_parses_embedded_object():
    from gemini_client import _strip_to_json

    text = "noise before {\n  \"topics\": []\n}\nnoise after"
    assert _strip_to_json(text) == {"topics": []}


def test_strip_to_json_supports_json5():
    from gemini_client import _strip_to_json

    text = """
{ // comment allowed in json5
  topics: [
    { title: 'A', subtopics: [] },
  ],
}
"""
    parsed = _strip_to_json(text)
    assert isinstance(parsed, dict)
    assert parsed.get("topics") is not None


def test_strip_to_json_garbage_returns_empty_dict():
    from gemini_client import _strip_to_json

    text = "not json at all !!!"
    assert _strip_to_json(text) == {}


