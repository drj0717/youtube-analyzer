#!/usr/bin/env python3
"""Fetch YouTube transcript with multi-layer fallback.

Usage: python3 fetch_transcript.py <video_url_or_id>

Fallback chain:
  1. Manual English captions (en)
  2. Auto-generated English captions (en)
  3. Any available language
  4. yt-dlp subtitle extraction
"""

import json
import os
import subprocess
import sys

from utils import extract_video_id, format_timestamp, output_error, output_success, work_dir


def fetch_via_api(video_id: str) -> list[dict] | None:
    """Fetch transcript using youtube-transcript-api with language fallback."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    ytt_api = YouTubeTranscriptApi()

    # Try manual English first, then auto-generated, then any language
    try:
        transcript = ytt_api.fetch(video_id, languages=["en"])
        return _normalize_api_result(transcript, "en (manual)")
    except Exception:
        pass

    try:
        transcript = ytt_api.fetch(video_id, languages=["en"])
        return _normalize_api_result(transcript, "en (auto)")
    except Exception:
        pass

    # Try fetching transcript list to find any available language
    try:
        transcript_list = ytt_api.list(video_id)
        for t in transcript_list:
            try:
                transcript = ytt_api.fetch(video_id, languages=[t.language_code])
                return _normalize_api_result(transcript, t.language_code)
            except Exception:
                continue
    except Exception:
        pass

    return None


def _normalize_api_result(transcript, source: str) -> list[dict]:
    """Convert youtube-transcript-api result to our format."""
    segments = []
    for snippet in transcript:
        segments.append({
            "start": round(snippet.start, 2),
            "duration": round(snippet.duration, 2),
            "text": snippet.text,
            "timestamp": format_timestamp(snippet.start),
        })
    return segments


def fetch_via_ytdlp(video_id: str) -> list[dict] | None:
    """Fallback: extract subtitles using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    wd = work_dir(video_id)
    sub_file = os.path.join(wd, "subs")

    try:
        # Try auto-subs first, then regular subs
        for flag in ["--write-auto-sub", "--write-sub"]:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    flag,
                    "--sub-lang", "en",
                    "--sub-format", "json3",
                    "--convert-subs", "json3",
                    "-o", sub_file,
                    url,
                ],
                capture_output=True, text=True, timeout=60
            )
            # Look for the generated subtitle file
            for ext in [".en.json3", ".json3"]:
                path = sub_file + ext
                if os.path.exists(path):
                    return _parse_json3_subs(path)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def _parse_json3_subs(path: str) -> list[dict] | None:
    """Parse json3 subtitle format from yt-dlp."""
    try:
        with open(path) as f:
            data = json.load(f)
        segments = []
        for event in data.get("events", []):
            if "segs" not in event:
                continue
            text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if not text:
                continue
            start_ms = event.get("tStartMs", 0)
            dur_ms = event.get("dDurationMs", 0)
            start_s = start_ms / 1000.0
            segments.append({
                "start": round(start_s, 2),
                "duration": round(dur_ms / 1000.0, 2),
                "text": text,
                "timestamp": format_timestamp(start_s),
            })
        return segments if segments else None
    except (json.JSONDecodeError, KeyError):
        return None


def main():
    if len(sys.argv) < 2:
        output_error("Usage: python3 fetch_transcript.py <video_url_or_id>")

    video_id = extract_video_id(sys.argv[1])
    if not video_id:
        output_error(f"Could not extract video ID from: {sys.argv[1]}")

    # Try API first
    segments = fetch_via_api(video_id)
    source = "youtube-transcript-api"

    # Fallback to yt-dlp
    if not segments:
        segments = fetch_via_ytdlp(video_id)
        source = "yt-dlp"

    if not segments:
        output_error("No transcript available. Video may lack captions entirely.")

    # Save to file
    wd = work_dir(video_id)
    transcript_path = os.path.join(wd, "transcript.json")
    with open(transcript_path, "w") as f:
        json.dump(segments, f, indent=2)

    # Calculate total duration from last segment
    last = segments[-1]
    total_duration = last["start"] + last["duration"]

    output_success({
        "video_id": video_id,
        "source": source,
        "segment_count": len(segments),
        "total_duration": round(total_duration, 2),
        "total_duration_formatted": format_timestamp(total_duration),
        "transcript_path": transcript_path,
    })


if __name__ == "__main__":
    main()
