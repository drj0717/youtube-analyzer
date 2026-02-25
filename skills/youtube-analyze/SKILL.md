---
name: youtube-analyze
description: Analyze a YouTube video using transcript + intelligent visual frame extraction with Claude's native vision
argument-hint: <youtube-url> [--quick]
allowed-tools: Bash, Read, Glob, Grep, WebFetch
---

# YouTube Video Analyzer

You are analyzing a YouTube video. Follow these phases **sequentially**. The scripts are located at `~/projects/youtube/bin/`.

**Input**: `$ARGUMENTS` contains the YouTube URL and optional flags.

Parse the arguments:
- Extract the YouTube URL from `$ARGUMENTS`
- Check if `--quick` flag is present (transcript-only mode, skip visual phases)

---

## Phase 1: Fetch Transcript

Run the transcript fetcher:
```bash
python3 ~/projects/youtube/bin/fetch_transcript.py "<URL>"
```

Parse the JSON output. If it failed, tell the user and stop.

Then read the full transcript:
```bash
cat /tmp/yt-analyzer/<video-id>/transcript.json
```

Read and internalize the entire transcript content.

---

## Phase 2: Visual Timestamp Selection

**Skip this phase if `--quick` flag was used.**

Based on the transcript, identify **8-15 timestamps** where the visual content is likely critical to understanding. Look for:

- **UI demonstrations**: "click here", "as you can see", "on the screen", "this menu", "this button"
- **Code on screen**: "this code", "let me show you", "here's the function", code walkthroughs
- **Charts/diagrams**: "this chart shows", "in this diagram", references to visual data
- **Product shots**: "look at this", "here's the design", physical product demonstrations
- **Slide content**: transitions between topics in presentations, "on this slide"
- **Before/after comparisons**: "now watch", "compare this to"

**Rules for timestamp selection:**
- Minimum **30 seconds** apart between any two frames
- Distribute across the full video duration
- If the transcript has few visual cues, fall back to **uniform sampling** (evenly spaced across the video)
- Always include a frame near the **beginning** (first 30s) and near the **end** (last 10%)
- Prefer timestamps where the speaker is clearly referencing something visual

Output your selected timestamps as a JSON array of seconds, e.g., `[15.0, 45.5, 90.0, ...]`

---

## Phase 3: Download Video

**Skip this phase if `--quick` flag was used.**

```bash
python3 ~/projects/youtube/bin/download_video.py "<URL>"
```

Parse the JSON output. If the video already existed, note that. If download failed, fall back to transcript-only analysis and inform the user.

---

## Phase 4: Extract Frames

**Skip this phase if `--quick` flag was used.**

Using your timestamps from Phase 2:
```bash
python3 ~/projects/youtube/bin/extract_frames.py "<video-id>" '[<timestamp1>, <timestamp2>, ...]'
```

Parse the JSON output to get the list of extracted frame paths.

---

## Phase 5: Visual Analysis

**Skip this phase if `--quick` flag was used.**

Read each extracted frame image using the Read tool. For each frame:
1. Describe what you see in the frame
2. Connect it to the surrounding transcript content (what was being said at that timestamp)
3. Note any information visible on screen that **isn't** captured in the transcript (code, UI elements, text on slides, data in charts)

---

## Phase 6: Synthesis

Read the reference templates for guidance:
```
~/.claude/skills/youtube-analyze/reference.md
```

Produce a comprehensive analysis that includes:

### Header
- Video title, duration, and a one-line summary

### Key Takeaways
- 3-7 bullet points capturing the most important insights

### Detailed Summary
- Section-by-section breakdown following the video's structure
- Integrate visual observations naturally (e.g., "The presenter demonstrated [X] on screen at [timestamp]...")
- For code-heavy videos: transcribe key code snippets shown on screen
- For tutorial videos: capture step-by-step procedures including menu paths and UI elements
- For presentations: capture key slide content and data points

### Visual Highlights
- **Skip this section if `--quick` mode.**
- Notable things captured in frames that weren't in the transcript
- References to specific frames with timestamps

### Timestamps Index
- Key moments with timestamps for easy navigation

---

## Phase 7: Interactive Q&A

After presenting the analysis, tell the user:

> **I've analyzed this video. Ask me any follow-up questions!** I can also extract additional frames from specific timestamps if you need to see something I didn't capture.

When the user asks follow-up questions:
- Answer from the transcript and visual analysis you've already done
- If they ask about a specific visual moment you didn't capture, offer to extract a frame:
  ```bash
  python3 ~/projects/youtube/bin/extract_frames.py "<video-id>" '[<timestamp>]'
  ```
  Then read and describe the new frame.

---

## Phase 8: Cleanup Prompt

When the conversation about the video seems to be wrapping up (user says thanks, moves on, etc.), ask:

> **Want me to keep or delete the downloaded video?** It's stored at `/mnt/c/Users/drj07/Videos/yt-analyzer/<video-id>.mp4` (~X MB).

If they want to delete it, remove the video file and the temp directory:
```bash
rm -f /mnt/c/Users/drj07/Videos/yt-analyzer/<video-id>.mp4
rm -rf /tmp/yt-analyzer/<video-id>
```
