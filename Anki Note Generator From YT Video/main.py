import asyncio
import os
from typing import Optional

from transcript_extractor import extract_transcript
from groq_client import generate_topics_and_flashcards
from anki_creator import create_anki_deck
from yt_title import fetch_video_title


async def run(video_url: str, output_path: str, deck_name: Optional[str] = None) -> str:
    transcript = extract_transcript(video_url, language_preference=["en", "en-US", "en-GB"])
    topics, flashcards = await generate_topics_and_flashcards(transcript)
    deck_name = deck_name or fetch_video_title(video_url) or "Generated Deck"
    apkg_path = create_anki_deck(flashcards, deck_name=deck_name, output_path=output_path)
    return apkg_path


def _input_url() -> str:
    url = input("Enter YouTube video URL: ").strip()
    output_path = input("Enter output path: ").strip()
    if not url:
        raise SystemExit("No URL provided.")
    if not output_path:
        print("No output path provided, using default path.")
        output_path = os.path.join("", os.path.abspath(f"{url}.apkg"))
    return url, output_path


def main():
    url = os.environ.get("YOUTUBE_URL")
    if not url:
        url, output_path = _input_url()
    apkg_path = asyncio.run(run(url, output_path))
    print(f"Anki deck created successfully at: {apkg_path}")


if __name__ == "__main__":
    main()

def main():
    print("Hello from anki-note-generator-from-yt-video!")


if __name__ == "__main__":
    main()
