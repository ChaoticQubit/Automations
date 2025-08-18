# ruff: noqa
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas import TopicsResponse, FlashcardsResponse
from anki_creator import create_anki_deck

def test_topics_response_model():
    payload = {
        "topics": [
            {
                "title": "Algebra",
                "subtopics": [
                    {"title": "Lecture 1: Basics", "summary": "intro", "key_points": ["sets", "numbers"]}
                ],
            }
        ]
    }
    model = TopicsResponse.model_validate(payload)
    assert model.topics[0].title == "Algebra"
    assert model.topics[0].subtopics[0].title.startswith("Lecture")


def test_flashcards_response_and_deck(tmp_path: Path):
    payload = {
        "decks": [
            {
                "topic": "Algebra",
                "subtopic": "Lecture 1",
                "cards": [
                    {"type": "qa", "question": "What is 2+2?", "answer": "4"},
                    {
                        "type": "single_choice",
                        "question": "Pick 2+2",
                        "options": ["3", "4", "5"],
                        "correct_option": 1,
                    },
                    {
                        "type": "multiple_choice",
                        "question": "Even numbers",
                        "options": ["1", "2", "3", "4"],
                        "correct_options": [1, 3],
                    },
                    {
                        "type": "matching",
                        "question": "Match terms",
                        "pairs": [
                            {"left": "a", "right": "alpha"},
                            {"left": "b", "right": "beta"},
                        ],
                    },
                ],
            }
        ]
    }
    cards = FlashcardsResponse.model_validate(payload)
    out = tmp_path / "deck.apkg"
    path = create_anki_deck(cards, deck_name="Algebra", output_path=str(out))
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


