# YouTube Video Analyzer

A Claude Code skill + Python toolchain for deep YouTube video analysis using transcript extraction and intelligent visual frame sampling with Claude's native vision.

## What it does

Given a YouTube URL, it:
1. Fetches the full transcript (via `youtube-transcript-api` with `yt-dlp` fallback)
2. Reads the transcript and identifies timestamps where visual content is likely critical
3. Downloads the video and extracts frames at those timestamps
4. Analyzes each frame visually with Claude
5. Produces a comprehensive written analysis integrating audio + visual content

## Requirements

- Python 3.x
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) (`pip install yt-dlp`)
- [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) (`pip install youtube-transcript-api`)
- `ffmpeg` (for frame extraction)
- [Claude Code](https://github.com/anthropics/claude-code) (for the `/youtube-analyze` skill)

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/drj0717/youtube-analyzer.git ~/projects/youtube
```

### 2. Install Python dependencies

```bash
pip install youtube-transcript-api yt-dlp
```

### 3. Install the Claude Code skill

```bash
mkdir -p ~/.claude/skills
cp -r skills/youtube-analyze ~/.claude/skills/
```

### 4. Configure paths (optional)

Edit `bin/utils.py` to change:
- `TEMP_BASE` — where temp files are stored (default: `/tmp/yt-analyzer`)
- `VIDEO_STORAGE` — where downloaded videos are kept (default: `/mnt/c/Users/drj07/Videos/yt-analyzer`)

## Usage

In any Claude Code session:

```
/youtube-analyze https://www.youtube.com/watch?v=VIDEO_ID
```

Add `--quick` for transcript-only analysis (no video download or frame extraction):

```
/youtube-analyze https://youtu.be/VIDEO_ID --quick
```

## Project structure

```
bin/
├── utils.py            # Shared constants and helpers
├── fetch_transcript.py # Transcript fetching
├── download_video.py   # Video download via yt-dlp
└── extract_frames.py   # Frame extraction via ffmpeg

skills/
└── youtube-analyze/
    ├── SKILL.md        # Claude Code skill (8-phase orchestration)
    └── reference.md    # Video type analysis templates
```

## Notes

- On WSL2 with a Windows video storage path (`/mnt/c/...`), videos are downloaded to `/tmp/` first, then copied — yt-dlp's merge step fails directly on the Windows filesystem.
- Uses `--js-runtimes node` (not `nodejs`) for yt-dlp JS runtime on this system.
