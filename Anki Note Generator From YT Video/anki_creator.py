import hashlib
import os
from typing import Optional

import genanki

from schemas import FlashcardsResponse, Card, CardQA, CardSingleChoice, CardMultipleChoice, CardMatching


def _stable_id_from_name(name: str) -> int:
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()
    # genanki requires 32-bit unsigned int
    return int(h[:8], 16)


def _format_card_to_fields(card: Card) -> tuple[str, str, str]:
    if isinstance(card, CardQA):
        extra = card.explanation or ""
        return card.question, card.answer, extra
    if isinstance(card, CardSingleChoice):
        options_html = "<br/>".join(f"{idx+1}. {opt}" for idx, opt in enumerate(card.options))
        answer = f"Correct: {card.correct_option + 1}"
        extra = (card.explanation or "").strip()
        return card.question + "<br/><br/>" + options_html, answer, extra
    if isinstance(card, CardMultipleChoice):
        options_html = "<br/>".join(f"{idx+1}. {opt}" for idx, opt in enumerate(card.options))
        answer = "Correct: " + ", ".join(str(i + 1) for i in card.correct_options)
        extra = (card.explanation or "").strip()
        return card.question + "<br/><br/>" + options_html, answer, extra
    if isinstance(card, CardMatching):
        pairs_html = "<br/>".join(f"{p.left} → {p.right}" for p in card.pairs)
        q = card.question or "Match the following"
        return q, pairs_html, ""
    # Fallback
    return "Unsupported card", "", ""


def create_anki_deck(
    flashcards: FlashcardsResponse,
    deck_name: str = "Generated Deck",
    output_path: Optional[str] = None,
) -> str:
    """
    Create an Anki package containing multiple decks, one per topic/subtopic.

    - Each deck is named as "{topic}" or "{topic}::{subtopic}" to form hierarchy.
    - The exported filename will be derived from `deck_name` unless `output_path` is provided.
    """
    # Shared model across all decks
    model_id = _stable_id_from_name(deck_name + "::model")
    model = genanki.Model(
        model_id=model_id,
        name="UniversalCardModel",
        fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Extra"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Question}}",
                "afmt": "{{FrontSide}}<hr id=answer>{{Answer}}<br/><br/>{{Extra}}",
            }
        ],
    )

    # Build decks per topic/subtopic
    name_to_deck: dict[str, genanki.Deck] = {}

    def get_or_create_deck(name: str) -> genanki.Deck:
        d = name_to_deck.get(name)
        if d is None:
            d = genanki.Deck(deck_id=_stable_id_from_name(name), name=name)
            name_to_deck[name] = d
        return d

    for deck_cards in flashcards.decks:
        deck_full_name = deck_cards.topic
        if deck_cards.subtopic:
            deck_full_name = f"{deck_cards.topic}::{deck_cards.subtopic}"
        target_deck = get_or_create_deck(deck_full_name)

        for card in deck_cards.cards:
            q, a, extra = _format_card_to_fields(card)
            note = genanki.Note(model=model, fields=[q, a, extra])
            target_deck.add_note(note)

    # Package all decks together
    decks = list(name_to_deck.values()) or [genanki.Deck(_stable_id_from_name(deck_name), deck_name)]
    package = genanki.Package(decks)
    if output_path is None:
        safe_name = deck_name.replace(os.sep, "_").replace(" ", "_")
        output_path = os.path.join(output_path, f"{safe_name}.apkg")
    package.write_to_file(output_path)
    return output_path


