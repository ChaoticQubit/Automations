Run:

1. Export your Groq key:

```bash
export GROQ_API_KEY=your_key
```

2. Optional: If YouTube limits apply, set one of:

```bash
export YTDLP_PROXY="socks5://127.0.0.1:1080"
export YTDLP_COOKIES_BROWSER="chrome"
# or
export YTDLP_COOKIES_FILE="/path/to/cookies.txt"
```

3. Execute:

```bash
uv run python main.py
```

