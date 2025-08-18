## Automations

A collection of small automation projects and tools. This repository contains one primary subproject used to generate Anki decks from YouTube videos.

### Project structure

- `Anki Note Generator From YT Video/` — Generate Anki `.apkg` files from YouTube transcripts and LLM-generated flashcards.

### Quick start

1. Change into the subproject directory:

```bash
cd "Anki Note Generator From YT Video"
```

2. Export your Groq API key:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

3. Run the tool (interactive):

```bash
uv run python main.py
```

See the subproject `README.md` for full setup, configuration, and troubleshooting notes.
