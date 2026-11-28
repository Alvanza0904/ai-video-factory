#!/usr/bin/env python3
"""Fast structural tests for the education animation scene library."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import education_animation as edu


def main():
    edu.WORK.mkdir(exist_ok=True)
    topics = [
        "regenerative braking", "baterai LFP", "perbedaan BEV HEV PHEV",
        "charging AC dan DC", "cara kerja motor listrik",
    ]
    visuals = set()
    for topic in topics:
        scenes = edu.choose_script(topic, 60)
        if len(scenes) != 8:
            raise RuntimeError(f"Expected 8 narrative scenes for {topic}, got {len(scenes)}")
        if len(scenes) < 5:
            raise RuntimeError(f"Too few scenes for {topic}")
        for scene in scenes:
            image = edu.draw_frame(scene, 3, 12)
            if image.size != (edu.W, edu.H) or image.mode != "RGB":
                raise RuntimeError("Invalid generated scene frame.")
            visuals.add(scene["visual"])
    if len(visuals) < 8:
        raise RuntimeError("Animation library coverage is too small.")
    short = edu.choose_script("cara kerja motor listrik", 30)
    if len(short) != 5 or "?" not in short[0]["narration"]:
        raise RuntimeError("Short-form hook or scene pacing is missing.")
    custom = edu.choose_script("teknologi kendaraan masa depan", 60)
    if len(custom) != 8:
        raise RuntimeError("Custom topic fallback must also contain eight scenes.")
    subtitles = edu.make_subtitles(edu.choose_script("regenerative braking", 45), [4.0]*7)
    content = subtitles.read_text(encoding="utf-8")
    if "-->" not in content or "\\n" in content:
        raise RuntimeError("Subtitle file is malformed.")
    print(f"PASS: {len(topics)} education topics, 8-scene storytelling, {len(visuals)} visual types, hooks and timed subtitles.")


if __name__ == "__main__":
    main()
