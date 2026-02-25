#!/usr/bin/env python3
"""Download YouTube video via yt-dlp.

Usage: python3 download_video.py <video_url_or_id>

Downloads to /tmp/ first (Linux FS for reliable merge), then copies to
/mnt/c/Users/drj07/Videos/yt-analyzer/ for persistent storage.
"""

import glob
import os
import shutil
import subprocess
import sys

from utils import TEMP_BASE, VIDEO_STORAGE, extract_video_id, output_error, output_success, work_dir


def main():
    if len(sys.argv) < 2:
        output_error("Usage: python3 download_video.py <video_url_or_id>")

    video_id = extract_video_id(sys.argv[1])
    if not video_id:
        output_error(f"Could not extract video ID from: {sys.argv[1]}")

    url = f"https://www.youtube.com/watch?v={video_id}"
    final_path = os.path.join(VIDEO_STORAGE, f"{video_id}.mp4")

    # Skip download if already exists in persistent storage
    if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
        size_mb = os.path.getsize(final_path) / (1024 * 1024)
        title = _get_title(url)
        _create_symlink(video_id, final_path)
        output_success({
            "video_id": video_id,
            "path": final_path,
            "title": title,
            "size_mb": round(size_mb, 1),
            "already_existed": True,
        })

    # Download to /tmp/ first (Linux FS handles yt-dlp merge reliably)
    wd = work_dir(video_id)
    tmp_template = os.path.join(wd, f"{video_id}.%(ext)s")
    tmp_expected = os.path.join(wd, f"{video_id}.mp4")

    # Get title first (--print with --skip-download)
    title = _get_title(url)

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--js-runtimes", "node",
                "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", tmp_template,
                "--no-playlist",
                url,
            ],
            capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired:
        output_error("Download timed out after 10 minutes.")
    except FileNotFoundError:
        output_error("yt-dlp not found. Install it with: pip install yt-dlp")

    if result.returncode != 0:
        output_error(f"yt-dlp failed: {result.stderr.strip()[-500:]}")

    # Find the downloaded file (might have slightly different name)
    if not os.path.exists(tmp_expected):
        candidates = glob.glob(os.path.join(wd, f"{video_id}.*"))
        candidates = [c for c in candidates if c.endswith(('.mp4', '.mkv', '.webm'))]
        if candidates:
            tmp_expected = candidates[0]
        else:
            output_error(
                f"Download completed but file not found. "
                f"Files in {wd}: {os.listdir(wd)}"
            )
    size_mb = os.path.getsize(tmp_expected) / (1024 * 1024)

    # Copy to persistent Windows storage
    try:
        os.makedirs(VIDEO_STORAGE, exist_ok=True)
        shutil.copy2(tmp_expected, final_path)
        stored_path = final_path
    except OSError:
        # If Windows storage fails, keep in /tmp/
        stored_path = tmp_expected

    _create_symlink(video_id, stored_path)

    output_success({
        "video_id": video_id,
        "path": stored_path,
        "title": title,
        "size_mb": round(size_mb, 1),
        "already_existed": False,
    })


def _get_title(url: str) -> str:
    """Get video title without downloading."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--js-runtimes", "node", "--print", "%(title)s", "--skip-download", url],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    except Exception:
        return "Unknown"


def _create_symlink(video_id: str, video_path: str):
    """Create symlink in work dir pointing to the video file."""
    wd = work_dir(video_id)
    link_path = os.path.join(wd, "video.mp4")
    if os.path.islink(link_path) or os.path.exists(link_path):
        try:
            os.unlink(link_path)
        except OSError:
            return
    try:
        os.symlink(video_path, link_path)
    except OSError:
        pass


if __name__ == "__main__":
    main()
