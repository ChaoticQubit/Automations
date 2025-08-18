from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Subtopic(BaseModel):
    title: str
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None


class Topic(BaseModel):
    title: str
    subtopics: List[Subtopic] = Field(default_factory=list)


class TopicsResponse(BaseModel):
    topics: List[Topic] = Field(default_factory=list)


class CardQA(BaseModel):
    type: Literal["qa"] = "qa"
    question: str
    answer: str
    explanation: Optional[str] = None


class CardSingleChoice(BaseModel):
    type: Literal["single_choice"] = "single_choice"
    question: str
    options: List[str]
    correct_option: int
    explanation: Optional[str] = None


class CardMultipleChoice(BaseModel):
    type: Literal["multiple_choice"] = "multiple_choice"
    question: str
    options: List[str]
    correct_options: List[int]
    explanation: Optional[str] = None


class MatchingPair(BaseModel):
    left: str
    right: str


class CardMatching(BaseModel):
    type: Literal["matching"] = "matching"
    question: Optional[str] = None
    pairs: List[MatchingPair]


Card = CardQA | CardSingleChoice | CardMultipleChoice | CardMatching


class DeckCards(BaseModel):
    topic: str
    subtopic: Optional[str] = None
    cards: List[Card]


class FlashcardsResponse(BaseModel):
    decks: List[DeckCards] = Field(default_factory=list)


