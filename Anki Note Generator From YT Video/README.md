# Anki Note Generator From YT Video

Generate Anki `.apkg` flashcard decks from YouTube videos using transcripts and the Groq LLM.

Features
- Extracts transcripts (prefers human subtitles, falls back to auto-generated)
- Uses the Groq `openai/gpt-oss-120b` model to extract topics/subtopics and generate deterministic JSON flashcards
- Produces Anki decks (`.apkg`) using `genanki`, with decks named by `Topic` and `Topic::Subtopic`

Prerequisites
- Python 3.13+ (project requires >=3.13 in `pyproject.toml`)
- `uv`/`uvx` (as the package runner used in this repo)
- `yt-dlp` available in the environment (installed from pyproject)
- `GROQ_API_KEY` environment variable set

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
- Set Groq API key:

```bash
export GROQ_API_KEY="your_groq_api_key"
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

2. Non-interactive:

```bash
YOUTUBE_URL="https://www.youtube.com/watch?v=VIDEO_ID" GROQ_API_KEY="..." uv run python main.py
```

Output
- The tool writes a `.apkg` file containing one or more decks. Decks are named by topic and subtopic (e.g., `Topic` or `Topic::Subtopic`). The exported filename is derived from the video title by default.

Testing
- Run the test suite:

```bash
uv run pytest -q
```

Troubleshooting
- No transcript found: YouTube may block automated transcript access from your IP. Try setting `YTDLP_PROXY` or `YTDLP_COOKIES_BROWSER`/`YTDLP_COOKIES_FILE` to authenticate/download via a browser session.
- Groq API 404: Ensure `GROQ_API_KEY` is set and valid; the project uses the `groq` Python client.

Contributing
- Tests use `pytest`. Add tests under `tests/` and keep functions small and well-typed.

License
- Add your license here.
