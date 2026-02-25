#!/usr/bin/env python3
"""Extract frames from a downloaded YouTube video at specified timestamps.

Usage: python3 extract_frames.py <video_id> '<json_array_of_timestamps>'

Example: python3 extract_frames.py dQw4w9WgXcQ '[30.5, 65.0, 120.0]'

Timestamps are in seconds. Outputs 720p JPEGs to /tmp/yt-analyzer/<id>/frames/.
"""

import json
import os
import subprocess
import sys

from utils import VIDEO_STORAGE, extract_video_id, format_timestamp, frames_dir, output_error, output_success, work_dir


def find_video(video_id: str) -> str | None:
    """Find the video file for this video ID."""
    # Check persistent storage first
    mp4_path = os.path.join(VIDEO_STORAGE, f"{video_id}.mp4")
    if os.path.exists(mp4_path):
        return mp4_path

    # Check work dir symlink
    link_path = os.path.join(work_dir(video_id), "video.mp4")
    if os.path.exists(link_path):
        return os.path.realpath(link_path)

    return None


def extract_frame(video_path: str, timestamp: float, output_path: str) -> bool:
    """Extract a single frame at the given timestamp."""
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=-1:720",
                "-q:v", "2",
                "-y",
                output_path,
            ],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0 and os.path.exists(output_path)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    if len(sys.argv) < 3:
        output_error("Usage: python3 extract_frames.py <video_id> '<json_timestamps>'")

    video_id = sys.argv[1]
    # Validate it looks like a video ID
    if not extract_video_id(video_id):
        # Maybe it's a URL
        video_id = extract_video_id(video_id)
        if not video_id:
            output_error(f"Invalid video ID: {sys.argv[1]}")

    try:
        timestamps = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        output_error(f"Invalid JSON timestamps: {e}")

    if not isinstance(timestamps, list) or not timestamps:
        output_error("Timestamps must be a non-empty JSON array of numbers.")

    # Validate all timestamps are numbers
    for ts in timestamps:
        if not isinstance(ts, (int, float)):
            output_error(f"Invalid timestamp: {ts} (must be a number)")

    video_path = find_video(video_id)
    if not video_path:
        output_error(f"Video not found for {video_id}. Run download_video.py first.")

    fdir = frames_dir(video_id)
    extracted = []
    failed = []

    for ts in sorted(timestamps):
        ts_label = format_timestamp(ts).replace(":", "-")
        frame_path = os.path.join(fdir, f"frame_{ts_label}_{ts:.1f}s.jpg")

        if extract_frame(video_path, ts, frame_path):
            extracted.append({
                "timestamp": ts,
                "timestamp_formatted": format_timestamp(ts),
                "path": frame_path,
                "size_kb": round(os.path.getsize(frame_path) / 1024, 1),
            })
        else:
            failed.append({
                "timestamp": ts,
                "timestamp_formatted": format_timestamp(ts),
            })

    if not extracted:
        output_error("Failed to extract any frames.")

    output_success({
        "video_id": video_id,
        "frames_dir": fdir,
        "extracted_count": len(extracted),
        "failed_count": len(failed),
        "frames": extracted,
        "failed": failed,
    })


if __name__ == "__main__":
    main()
