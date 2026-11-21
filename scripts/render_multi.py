#!/usr/bin/env python3
"""Multi-clip FFmpeg smoke renderer for AI Video Factory.

This is infrastructure validation only. AI scene selection, transitions, audio
design, and editing-blueprint execution are implemented in later phases.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

WORK = Path("render-work")
MAX_CLIPS = 10
MAX_BYTES_PER_CLIP = 500 * 1024 * 1024


def run(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def safe_download(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Only HTTPS video URLs are accepted.")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AI-Video-Factory-Render/0.1"},
    )
    total = 0
    with urllib.request.urlopen(request, timeout=60) as response:
        final_url = urlparse(response.geturl())
        if final_url.scheme != "https":
            raise ValueError("Download redirected to a non-HTTPS URL.")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_BYTES_PER_CLIP:
            raise ValueError("A source clip exceeds the 500 MB limit.")
        with destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES_PER_CLIP:
                    raise ValueError("A source clip exceeds the 500 MB limit.")
                output.write(chunk)
    if total == 0:
        raise ValueError("Downloaded source clip is empty.")


def probe_duration(path: Path) -> float:
    value = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ])
    duration = float(value)
    if duration <= 0:
        raise ValueError("Could not read a valid video duration.")
    return duration


def has_audio(path: Path) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True
    )
    return bool(result.stdout.strip())


def main() -> None:
    urls = [line.strip() for line in os.environ.get("SOURCE_URLS", "").splitlines() if line.strip()]
    if not 1 <= len(urls) <= MAX_CLIPS:
        raise ValueError(f"Provide between 1 and {MAX_CLIPS} HTTPS video URLs.")
    target = int(os.environ.get("DURATION_SECONDS", "45"))
    if target not in (30, 45, 60):
        raise ValueError("Target duration must be 30, 45, or 60 seconds.")
    output_name = os.environ.get("OUTPUT_NAME", "ai-video-factory-output")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", output_name):
        raise ValueError("Invalid output filename.")

    WORK.mkdir(exist_ok=True)
    normalized: list[Path] = []
    segment = target / len(urls)

    for index, url in enumerate(urls, start=1):
        source = WORK / f"source-{index:02d}"
        safe_download(url, source)
        source_duration = probe_duration(source)
        segment_duration = segment if index < len(urls) else target - segment * (len(urls) - 1)
        if source_duration < segment_duration:
            print(f"Clip {index}: source is shorter than its segment; it will loop to fill the slot.")
        audio_present = has_audio(source)
        normalized_path = WORK / f"normalized-{index:02d}.mp4"

        base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", str(source)]
        if audio_present:
            command = base + [
                "-t", f"{segment_duration:.3f}",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
                "-af", "aresample=48000,apad",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", str(normalized_path)
            ]
        else:
            command = base + [
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-t", f"{segment_duration:.3f}", "-map", "0:v:0", "-map", "1:a:0",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", str(normalized_path)
            ]
        run(command)
        normalized.append(normalized_path)
        print(f"Prepared clip {index}/{len(urls)}.")

    concat_file = WORK / "concat.txt"
    concat_file.write_text(
        "".join(f"file '{path.resolve().as_posix()}'\n" for path in normalized),
        encoding="utf-8"
    )
    output = Path(f"{output_name}.mp4")
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", "-movflags", "+faststart", str(output)
    ])
    metadata = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,width,height",
        "-of", "json", str(output)
    ])
    print("Render complete.")
    print(json.dumps(json.loads(metadata), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"RENDER FAILED: {error}", file=sys.stderr)
        sys.exit(1)
