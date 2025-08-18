import subprocess
import json
from typing import Optional


def fetch_video_title(url: str) -> Optional[str]:
    """Fetch the YouTube video title using yt-dlp metadata extraction."""
    cmd = [
        "python",
        "-m",
        "yt_dlp",
        "--skip-download",
        "--dump-single-json",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        title = data.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    except Exception:
        return None
    return None


