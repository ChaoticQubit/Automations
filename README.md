## Automations

A collection of small automation projects and tools. This repository currently contains one primary subproject that generates Anki decks from YouTube videos.

### Project structure

- `Anki Note Generator From YT Video/` — Generate Anki `.apkg` files from YouTube transcripts and LLM-generated flashcards. The tool supports both Groq and Google Gemini providers.

### Quick start

1. Change into the subproject directory:

```bash
cd "Anki Note Generator From YT Video"
```

2. Export an API key for your chosen provider. Either:

```bash
# Groq
export GROQ_API_KEY="your_groq_api_key"
# or (alternate name supported)
export GROQ_API_TOKEN="your_groq_api_token"

# Google Gemini
export GOOGLE_API_KEY="your_google_api_key"
# or
export GEMINI_API_KEY="your_gemini_api_key"
```

3. (Optional) Select a provider/model via env vars:

```bash
export LLM_PROVIDER="groq"    # or "gemini"
export LLM_MODEL="openai/gpt-oss-120b"  # or a Gemini model like "gemini-1.5-pro"
```

4. Run the tool (interactive):

```bash
uv run python main.py
```

See the subproject `README.md` for full setup, configuration, and troubleshooting notes.
