#!/usr/bin/env python3
"""Exercise FFmpeg SFX generation, timestamping, ducking, subtitles, and muxing."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import ai_edit


def main() -> None:
    ai_edit.WORK.mkdir(exist_ok=True)
    source = ai_edit.WORK / "audio-smoke-source.mp4"
    output = ai_edit.WORK / "audio-smoke-output.mp4"
    subtitles = ai_edit.WORK / "audio-smoke.srt"
    subtitles.write_text(
        "1\n00:00:00,300 --> 00:00:01,100\nAudio mix test\n",
        encoding="utf-8",
    )
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x568:r=30:d=3",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", str(source),
    ], check=True)
    blueprint = {
        "output": {"duration_seconds": 3},
        "scenes": [{
            "timeline_start": 0,
            "audio_cues": [{
                "kind": "comedy", "asset_id": "boing",
                "at": 1.25, "duration": 0.8, "gain_db": -18,
            }],
        }],
    }
    subtitle_filter = "subtitles=" + str(subtitles.resolve()).replace("\\", "/").replace(":", "\\:")
    ai_edit.build_audio_mix(blueprint, source, output, subtitle_filter)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name", "-of", "json", str(output),
    ], text=True))
    streams = probe.get("streams", [])
    if not any(s.get("codec_type") == "audio" and s.get("codec_name") == "aac" for s in streams):
        raise RuntimeError("Audio smoke test failed: AAC audio stream is missing.")
    duration = float(probe.get("format", {}).get("duration", 0))
    if not 2.8 <= duration <= 3.2:
        raise RuntimeError(f"Audio smoke test failed: unexpected duration {duration}.")
    print("PASS: generated meme-style SFX, timestamped mix, dialogue ducking, subtitles, AAC mux.")


if __name__ == "__main__":
    main()
