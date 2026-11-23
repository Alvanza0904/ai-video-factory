#!/usr/bin/env python3
"""Offline regression test for the multi-clip xfade normalization graph."""
import json
import subprocess
import tempfile
from pathlib import Path


def run(command):
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-5000:])


def main():
    with tempfile.TemporaryDirectory(prefix="avf-xfade-") as directory:
        root = Path(directory)
        clips = [root / "a.mp4", root / "b.mp4"]
        specs = [
            ("640x360", "24", "440"),
            ("720x1280", "60", "660"),
        ]
        for path, (size, fps, tone) in zip(clips, specs):
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={fps}:duration=2",
                "-f", "lavfi", "-i", f"sine=frequency={tone}:sample_rate=44100:duration=2",
                "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", str(path),
            ])
        output = root / "joined.mp4"
        graph = (
            "[0:v]fps=30,scale=360:640,setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v0];"
            "[0:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];"
            "[1:v]fps=30,scale=360:640,setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v1];"
            "[1:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];"
            "[v0][v1]xfade=transition=fade:duration=0.2:offset=1.8[v];"
            "[a0][a1]acrossfade=d=0.2:c1=tri:c2=tri[a]"
        )
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(clips[0]), "-i", str(clips[1]),
            "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-movflags", "+faststart", str(output),
        ])
        info = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(output),
        ], text=True))
        duration = float(info["format"]["duration"])
        if not 3.5 <= duration <= 4.0:
            raise RuntimeError(f"Unexpected xfade output duration: {duration:.3f}s")
        print(f"xfade regression passed: mixed 24/60 fps clips, output {duration:.3f}s")


if __name__ == "__main__":
    main()
