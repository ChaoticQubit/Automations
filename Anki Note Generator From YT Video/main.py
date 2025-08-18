import asyncio
import os
from typing import Optional
from questionary import select

from transcript_extractor import extract_transcript
from model_selection import list_models, get_generator
from anki_creator import create_anki_deck
from yt_title import fetch_video_title


async def run(video_url: str, output_path: str, deck_name: Optional[str] = None) -> str:
    transcript = extract_transcript(video_url, language_preference=["en", "en-US", "en-GB"])
    provider = (os.environ.get("LLM_PROVIDER") or "groq").strip().lower()
    model = os.environ.get("LLM_MODEL")
    generator = get_generator(provider)
    topics, flashcards = await generator(transcript, model)
    deck_name = deck_name or fetch_video_title(video_url) or "Generated Deck"
    apkg_path = create_anki_deck(flashcards, deck_name=deck_name, output_path=output_path)
    return apkg_path


def _input_url() -> str:
    url = input("Enter YouTube video URL: ").strip()
    output_path = input("Enter output path: ").strip()
    # allow interactive provider/model selection (use questionary for arrow-key selection if available)
    try:
        available = list_models()
        try:
            provider_choice = select(
                "Choose provider:", choices=list(available.keys()), default="groq"
            ).ask()
            provider = (provider_choice or "groq").strip().lower()

            model_choice = None
            provider_models = available.get(provider, [])
            if provider_models:
                # offer a "<use default>" sentinel so user can keep default model
                choices = provider_models + ["<use default>"]
                model_choice = select(
                    "Choose model (or <use default>):", choices=choices
                ).ask()

            if provider:
                os.environ["LLM_PROVIDER"] = provider
            if model_choice and model_choice != "<use default>":
                os.environ["LLM_MODEL"] = model_choice
        except Exception:
            # fallback to text input if questionary isn't available or fails
            print("Available providers and models:")
            for prov, models in available.items():
                print(f"- {prov}: {', '.join(models[:5])}{' ...' if len(models) > 5 else ''}")
            provider = input("Choose provider [groq/gemini] (default groq): ").strip().lower() or "groq"
            model = input("Optional: choose specific model (leave blank to use default): ").strip()
            if provider:
                os.environ["LLM_PROVIDER"] = provider
            if model:
                os.environ["LLM_MODEL"] = model
    except Exception:
        pass
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
