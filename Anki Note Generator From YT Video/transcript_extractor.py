import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Optional, Iterable

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


def _parse_json3_to_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    text_fragments: list[str] = []
    for event in data.get("events", []):
        for seg in event.get("segs", []) or []:
            frag = seg.get("utf8")
            if frag:
                text_fragments.append(frag)
    return "".join(text_fragments).strip()


def _normalize_langs(langs: Optional[Iterable[str]]) -> list[str]:
    if not langs:
        return ["en"]
    normalized: list[str] = []
    for lang in langs:
        if lang == "en":
            # Include regional variants when user specifies 'en'
            normalized.extend(["en", "en.*"])
        else:
            normalized.append(lang)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for normalized_lang in normalized:
        if normalized_lang not in seen:
            seen.add(normalized_lang)
            result.append(normalized_lang)
    return result


def _run_ytdlp_for_subs(
    video_url: str,
    work_dir: str,
    manual_subs: bool,
    language_preference: Optional[list[str]] = None,
) -> list[str]:
    """
    Run yt-dlp to fetch subtitles (json3) into work_dir and return list of created .json3 files.
    If manual_subs is True, tries human subtitles only, else auto-generated.
    """
    language_preference = _normalize_langs(language_preference)

    # Output template without extension so subtitle language and ext are appended
    output_template = os.path.join(work_dir, "%(id)s")

    # Build base command
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--no-progress",
        "--sub-format",
        "json3",
        "--sub-langs",
        ",".join(language_preference),
        "-o",
        output_template,
    ]

    # Optional proxy/cookies via env
    proxy = os.getenv("YTDLP_PROXY")
    if proxy:
        cmd += ["--proxy", proxy]
    cookies_browser = os.getenv("YTDLP_COOKIES_BROWSER")
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cookies_file = os.getenv("YTDLP_COOKIES_FILE")
    if cookies_file:
        cmd += ["--cookies", cookies_file]

    cmd.append(video_url)
    if manual_subs:
        cmd.insert(1, "--write-sub")
    else:
        cmd.insert(1, "--write-auto-sub")

    # Try running as module to favor uv environment
    try_cmd = ["python", "-m", "yt_dlp"] + cmd[1:]
    result = subprocess.run(try_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback to direct binary name
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Still return whatever files might have been produced if any
        pass

    return sorted(glob.glob(os.path.join(work_dir, "*.json3")))


def _run_ytdlp_for_subs_both(
    video_url: str,
    work_dir: str,
    language_preference: Optional[list[str]] = None,
) -> list[str]:
    """Attempt downloading both manual and auto subtitles in all available languages."""
    language_preference = ["all"]
    output_template = os.path.join(work_dir, "%(id)s")
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--no-progress",
        "--sub-format",
        "json3",
        "--sub-langs",
        ",".join(language_preference),
        "--write-sub",
        "--write-auto-sub",
        "-o",
        output_template,
    ]
    proxy = os.getenv("YTDLP_PROXY")
    if proxy:
        cmd += ["--proxy", proxy]
    cookies_browser = os.getenv("YTDLP_COOKIES_BROWSER")
    if cookies_browser:
        cmd += ["--cookies-from-browser", cookies_browser]
    cookies_file = os.getenv("YTDLP_COOKIES_FILE")
    if cookies_file:
        cmd += ["--cookies", cookies_file]
    cmd.append(video_url)

    try_cmd = ["python", "-m", "yt_dlp"] + cmd[1:]
    result = subprocess.run(try_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        result = subprocess.run(cmd, capture_output=True, text=True)
    return sorted(glob.glob(os.path.join(work_dir, "*.json3")))


def _yt_dlp_list_subs_output(video_url: str) -> str:
    cmd = ["yt-dlp", "--list-subs", video_url]
    try_cmd = ["python", "-m", "yt_dlp"] + cmd[1:]
    result = subprocess.run(try_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        result = subprocess.run(cmd, capture_output=True, text=True)
    return (result.stdout or result.stderr or "").strip()


def _parse_list_subs_codes(output: str) -> list[str]:
    # yt-dlp --list-subs prints a table; parse language codes from lines like:
    # en        vtt, ttml, srv3, ...
    codes: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Language") or line.startswith("Available subtitles"):
            continue
        parts = line.split()
        if parts and re.match(r"^[a-z]{2}(-[A-Za-z0-9]+)*$", parts[0]):
            codes.append(parts[0])
    # Deduplicate
    return list(dict.fromkeys(codes))


def extract_transcript(
    video_url: str,
    language_preference: Optional[list[str]] = None,
    working_directory: Optional[str] = None,
) -> str:
    """
    Extract transcript using yt-dlp. Prefer human subtitles; fallback to auto.
    Returns transcript text or raises Exception on failure.
    """
    temp_dir = None
    work_dir = working_directory
    try:
        if work_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="yt_transcript_")
            work_dir = temp_dir

        # First: try human subtitles
        manual_files = _run_ytdlp_for_subs(
            video_url, work_dir, manual_subs=True, language_preference=language_preference
        )
        files_to_parse = manual_files

        # Fallback: auto-generated
        if not files_to_parse:
            auto_files = _run_ytdlp_for_subs(
                video_url, work_dir, manual_subs=False, language_preference=language_preference
            )
            files_to_parse = auto_files

        # Final yt-dlp attempt: try both manual and auto, all languages
        if not files_to_parse:
            both_files = _run_ytdlp_for_subs_both(
                video_url, work_dir, language_preference=language_preference or ["all"]
            )
            files_to_parse = both_files

        if not files_to_parse:
            # Final fallback: youtube-transcript-api (prefer manual, then auto)
            try:
                vid = _extract_video_id(video_url)
                lp = language_preference or ["en", "en-US", "en-GB"]
                api = YouTubeTranscriptApi()
                transcripts = api.list(vid)

                # Try manually created transcripts first
                for lang in lp:
                    try:
                        tr = transcripts.find_manually_created_transcript([lang])
                        items = tr.fetch()
                        text = " ".join(item.get("text", "") for item in items if item.get("text"))
                        if text.strip():
                            return text.strip()
                    except Exception:
                        continue

                # Fallback: auto-generated transcripts
                for lang in lp:
                    try:
                        tr = transcripts.find_generated_transcript([lang])
                        items = tr.fetch()
                        text = " ".join(item.get("text", "") for item in items if item.get("text"))
                        if text.strip():
                            return text.strip()
                    except Exception:
                        continue
            except (NoTranscriptFound, TranscriptsDisabled):
                pass
            # As a helpful hint, include available subs listing (truncated)
            try:
                subs_info = _yt_dlp_list_subs_output(video_url)
            except Exception:
                subs_info = ""
            msg = "No transcript found or generated."
            if subs_info:
                msg += " Available subtitles info (yt-dlp --list-subs):\n" + subs_info[:1500]
            raise Exception(msg)

        # Prefer language order provided
        selected_file = files_to_parse[0]
        if language_preference:
            # Try to match exact language code in file name first; then prefix matches (e.g., en, en-US)
            for lang in language_preference:
                candidates = [p for p in files_to_parse if f".{lang}.json3" in p]
                if candidates:
                    selected_file = candidates[0]
                    break
            else:
                # prefix match like ".en-"
                for lang in language_preference:
                    prefix_candidates = [p for p in files_to_parse if f".{lang.split('-')[0]}-" in p]
                    if prefix_candidates:
                        selected_file = prefix_candidates[0]
                        break

        transcript = _parse_json3_to_text(selected_file)
        if not transcript:
            raise Exception("Transcript is empty.")
        return transcript
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def _extract_video_id(url: str) -> str:
    # Handle https://youtu.be/<id>, https://www.youtube.com/watch?v=<id>
    # and common variants with params
    m = re.search(r"youtu\.be/([\w-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"v=([\w-]{11})", url)
    if m:
        return m.group(1)
    # Best-effort fallback
    m = re.search(r"([\w-]{11})", url)
    if m:
        return m.group(1)
    raise ValueError("Could not extract YouTube video ID")


