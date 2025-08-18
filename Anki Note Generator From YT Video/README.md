# Anki Note Generator From YT Video

Generate Anki `.apkg` flashcard decks from YouTube videos using transcripts and an LLM. This project supports both Groq and Google Gemini providers.

Features
- **Transcript extraction**: prefers human subtitles, falls back to auto-generated transcripts.
- **Multi-provider LLM support**: works with Groq (`openai/gpt-oss-120b` by default) and Google Gemini (`gemini-1.5-pro` by default).
- **Deterministic JSON flashcards**: LLM output is parsed into strict JSON and validated against typed schemas.
- **Anki export**: produces `.apkg` files using `genanki`, with decks organized by `Topic` and `Topic::Subtopic`.

Prerequisites
- **Python 3.13+** (see `pyproject.toml`)
- **`uv`/`uvx`** (used as the package runner)
- **`yt-dlp`** (available via `pyproject.toml` dependencies)
- **One of the provider API keys** set in the environment:
  - Groq: `GROQ_API_KEY` or `GROQ_API_TOKEN`
  - Google Gemini: `GOOGLE_API_KEY` or `GEMINI_API_KEY`

Installation
1. Change into the project directory:

```bash
cd "Anki Note Generator From YT Video"
```

2. Install dependencies via `uv`:

```bash
uv pip install -r requirements.txt  # or rely on uv to install from pyproject
```

Configuration
- Export an API key for your chosen provider:

```bash
# Groq
export GROQ_API_KEY="your_groq_api_key"
# or
export GROQ_API_TOKEN="your_groq_api_token"

# Google Gemini
export GOOGLE_API_KEY="your_google_api_key"
# or
export GEMINI_API_KEY="your_gemini_api_key"
```

- Optionally set provider/model selection:

```bash
export LLM_PROVIDER="groq"    # or "gemini"
export LLM_MODEL="openai/gpt-oss-120b"  # or a Gemini model like "gemini-1.5-pro"
```

- Optional (workarounds for YouTube blocking):

```bash
export YTDLP_PROXY="socks5://127.0.0.1:1080"
export YTDLP_COOKIES_BROWSER="chrome"
# or
export YTDLP_COOKIES_FILE="/path/to/cookies.txt"
```

Usage
1. Interactive (prompts for URL and output path):

```bash
uv run python main.py
```

2. Non-interactive (examples):

```bash
# Groq, non-interactive
YOUTUBE_URL="https://www.youtube.com/watch?v=VIDEO_ID" GROQ_API_KEY="..." uv run python main.py

# Gemini, non-interactive
YOUTUBE_URL="https://www.youtube.com/watch?v=VIDEO_ID" GOOGLE_API_KEY="..." LLM_PROVIDER="gemini" uv run python main.py
```

Output
- The tool writes a `.apkg` file containing one or more decks. Deck names are derived from topic and subtopic (e.g., `Topic` or `Topic::Subtopic`). The exported filename is derived from the video title by default.

Testing
- Run the test suite:

```bash
uv run pytest -q
```

Troubleshooting
- **No transcript found**: YouTube may block automated transcript access from your IP. Try setting `YTDLP_PROXY` or `YTDLP_COOKIES_BROWSER`/`YTDLP_COOKIES_FILE` to authenticate/download via a browser session.
- **API key errors**: Ensure the correct provider API key env var is set (`GROQ_API_KEY` / `GROQ_API_TOKEN` for Groq, `GOOGLE_API_KEY` / `GEMINI_API_KEY` for Gemini). The project uses the `groq` and `google-genai` clients where appropriate.

Contributing
- Tests use `pytest`. Add tests under `tests/` and keep functions small and well-typed.

License
- Add your license here.
