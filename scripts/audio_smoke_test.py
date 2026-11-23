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
    # Also exercise a real two-scene video/audio transition, not just an audio-only mux.
    clip_a = ai_edit.WORK / "transition-scene-a.mp4"
    clip_b = ai_edit.WORK / "transition-scene-b.mp4"
    for path, color, frequency in [(clip_a, "0x24364b", 330), (clip_b, "0x80613a", 550)]:
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x568:r=30:d=1.6",
            "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=1.6",
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(path),
        ], check=True)
    previous_output = ai_edit.OUTPUT
    ai_edit.OUTPUT = ai_edit.WORK / "transition-smoke-output.mp4"
    transition_blueprint = {
        "output": {"duration_seconds": 2.96},
        "scenes": [
            {"scene_id": "one", "asset_id": "a", "source_in": 0, "source_out": 1.6,
             "timeline_start": 0, "timeline_end": 1.6, "transition_in": "cut",
             "visual_profile": "natural", "captions": [], "audio_cues": []},
            {"scene_id": "two", "asset_id": "b", "source_in": 0, "source_out": 1.6,
             "timeline_start": 1.6, "timeline_end": 3.2, "transition_in": "dissolve",
             "visual_profile": "natural", "captions": [], "audio_cues": []},
        ],
    }
    ai_edit.render(transition_blueprint, [
        {"id": "a", "path": str(clip_a), "duration": 1.6},
        {"id": "b", "path": str(clip_b), "duration": 1.6},
    ])
    transition_probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name", "-of", "json", str(ai_edit.OUTPUT),
    ], text=True))
    if not any(s.get("codec_name") == "h264" for s in transition_probe.get("streams", [])):
        raise RuntimeError("Scene transition smoke test failed: H.264 video missing.")
    transition_duration = float(transition_probe.get("format", {}).get("duration", 0))
    if not 2.6 <= transition_duration <= 3.1:
        raise RuntimeError(f"Scene transition smoke test failed: unexpected duration {transition_duration}.")
    ai_edit.OUTPUT = previous_output
    print("PASS: generated SFX, audio mix, dialogue ducking, subtitles, and rendered scene-to-scene dissolve/audio crossfade.")


if __name__ == "__main__":
    main()
