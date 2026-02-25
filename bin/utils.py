"""Shared utilities for YouTube video analyzer."""

import json
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

# Path constants
TEMP_BASE = "/tmp/yt-analyzer"
VIDEO_STORAGE = "/mnt/c/Users/drj07/Videos/yt-analyzer"
BIN_DIR = os.path.dirname(os.path.abspath(__file__))


def extract_video_id(url_or_id: str) -> str | None:
    """Extract YouTube video ID from various URL formats or a raw ID."""
    # Already a video ID (11 chars, alphanumeric + - + _)
    if re.match(r'^[A-Za-z0-9_-]{11}$', url_or_id):
        return url_or_id

    # Try parsing as URL
    parsed = urlparse(url_or_id)
    host = parsed.hostname or ""

    # youtu.be/VIDEO_ID
    if host in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/").split("/")[0]
        if re.match(r'^[A-Za-z0-9_-]{11}$', vid):
            return vid

    # youtube.com/watch?v=VIDEO_ID
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            v = qs.get("v", [None])[0]
            if v and re.match(r'^[A-Za-z0-9_-]{11}$', v):
                return v
        # youtube.com/embed/VIDEO_ID or youtube.com/v/VIDEO_ID
        for prefix in ("/embed/", "/v/", "/shorts/"):
            if parsed.path.startswith(prefix):
                vid = parsed.path[len(prefix):].split("/")[0].split("?")[0]
                if re.match(r'^[A-Za-z0-9_-]{11}$', vid):
                    return vid

    return None


def work_dir(video_id: str) -> str:
    """Return and create the temp working directory for a video."""
    d = os.path.join(TEMP_BASE, video_id)
    os.makedirs(d, exist_ok=True)
    return d


def frames_dir(video_id: str) -> str:
    """Return and create the frames directory for a video."""
    d = os.path.join(work_dir(video_id), "frames")
    os.makedirs(d, exist_ok=True)
    return d


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def output_success(data: dict) -> None:
    """Print a structured success JSON to stdout and exit."""
    print(json.dumps({"success": True, "data": data}))
    sys.exit(0)


def output_error(message: str) -> None:
    """Print a structured error JSON to stdout and exit with code 1."""
    print(json.dumps({"success": False, "error": message}))
    sys.exit(1)
