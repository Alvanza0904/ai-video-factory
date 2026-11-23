#!/usr/bin/env python3
"""Cloud AI director: inspect footage, transcribe speech, plan and render a vertical edit."""
from __future__ import annotations

import base64
import json
import math
import random
import struct
import wave
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(".")
WORK = ROOT / "ai-edit-work"
OUTPUT = ROOT / "ai-video-factory-final.mp4"
BASE_URL = os.environ.get("RELINK_BASE_URL", "https://api.relink-gateway.biz.id/v1").rstrip("/")
API_KEY = os.environ.get("RELINK_API_KEY", "")
VISION_MODEL = os.environ.get("RELINK_VISION_MODEL", "deepseek-v4.1-flash")


def run(command: list[str], *, capture: bool = True) -> str:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "No FFmpeg diagnostic output").strip()
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(str(part) for part in command[:8])} ...\\n"
            f"Technical detail: {detail[-7000:]}"
        )
    return result.stdout.strip() if capture else ""


def api_json(url: str, payload: dict, timeout: int = 180) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Re:Link AI returned HTTP {error.code}. Verify the configured model and API access.") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Cannot connect to Re:Link AI: {error.reason}") from None


def load_manifest() -> dict:
    params = urllib.parse.urlencode({"job_id": os.environ["JOB_ID"], "run_id": os.environ["GITHUB_RUN_ID"]})
    request = urllib.request.Request(os.environ["MANIFEST_URL"] + "?" + params,
        headers={"Authorization": "Bearer " + os.environ["OIDC_TOKEN"], "Accept": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            manifest = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Could not load private job manifest (HTTP {error.code}): {detail}") from None
    os.environ["USER_ID"] = manifest["userId"]
    os.environ["PROJECT_ID"] = manifest["projectId"]
    os.environ["JOB_EXPIRES"] = manifest["expires"]
    os.environ["JOB_SIGNATURE"] = manifest["signature"]
    os.environ["ASSETS_JSON"] = json.dumps(manifest["assets"])
    os.environ["TARGET_DURATION"] = str(manifest["targetDuration"])
    os.environ["SELECTED_GENRE"] = manifest["genre"]
    os.environ["EDIT_INSTRUCTIONS"] = manifest.get("instructions", "")
    return manifest


def download_assets() -> list[dict]:
    assets = json.loads(os.environ["ASSETS_JSON"])
    if not isinstance(assets, list) or not 1 <= len(assets) <= 10:
        raise ValueError("The job must contain 1–10 uploaded clips.")
    base = os.environ["DOWNLOAD_BASE_URL"]
    params = {
        "job_id": os.environ["JOB_ID"],
        "user_id": os.environ["USER_ID"],
        "expires": os.environ["JOB_EXPIRES"],
        "signature": os.environ["JOB_SIGNATURE"],
    }
    output = []
    for index, asset in enumerate(assets, start=1):
        query = urllib.parse.urlencode({**params, "key": asset["key"], "run_id": os.environ["GITHUB_RUN_ID"]})
        url = base + "?" + query
        path = WORK / f"source-{index:02d}.mov"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36", "Authorization": "Bearer " + os.environ["OIDC_TOKEN"]})
        with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as file:
            while chunk := response.read(1024 * 1024):
                file.write(chunk)
        if path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded clip {index} is empty.")
        meta = json.loads(run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
            "-of", "json", str(path)
        ]))
        duration = float(meta.get("format", {}).get("duration", 0))
        if duration <= 0:
            raise RuntimeError(f"Cannot read the duration of clip {index}.")
        output.append({**asset, "path": str(path), "duration": duration, "probe": meta})
        print(f"Downloaded {index}/{len(assets)}: {asset.get('filename', path.name)} ({duration:.1f}s)")
    return output


def transcribe(assets: list[dict]) -> dict[str, list[dict]]:
    """Small local Whisper model runs on the GitHub-hosted runner; no extra speech API key."""
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    transcripts: dict[str, list[dict]] = {}
    for asset in assets:
        audio = WORK / (Path(asset["path"]).stem + ".wav")
        audio_probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", asset["path"]], capture_output=True, text=True).stdout.strip()
        if not audio_probe:
            transcripts[asset["id"]] = []
            continue
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", asset["path"],
            "-vn", "-ac", "1", "-ar", "16000", str(audio)
        ], check=True, capture_output=True)
        segments, _ = model.transcribe(str(audio), vad_filter=True, beam_size=5, word_timestamps=True)
        transcripts[asset["id"]] = [
            {
                "start": round(s.start, 2),
                "end": round(s.end, 2),
                "text": s.text.strip(),
                "words": [
                    {"start": round(w.start, 2), "end": round(w.end, 2), "text": w.word}
                    for w in (s.words or [])
                ]
            }
            for s in segments if s.text.strip()
        ]
    return transcripts


def sample_frames(assets: list[dict]) -> tuple[list[dict], list[dict]]:
    images: list[dict] = []
    frame_map: list[dict] = []
    for asset in assets:
        # Dense visual sampling across the whole clip, rather than three arbitrary frames.
        duration = float(asset["duration"])
        sample_count = min(10, max(3, int(duration // 2.5) + 1))
        timestamps = [duration * (i + 0.5) / sample_count for i in range(sample_count)]
        for frame_index, timestamp_value in enumerate(timestamps, start=1):
            timestamp = max(0.05, min(duration - 0.05, timestamp_value))
            image_path = WORK / f"{asset['id'][:8]}-frame-{frame_index:02d}.jpg"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(timestamp),
                "-i", asset["path"], "-frames:v", "1", "-vf", "scale=640:-2",
                "-q:v", "6", str(image_path)
            ], check=True, capture_output=True)
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            images.append({
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64," + encoded, "detail": "high"}
            })
            frame_map.append({
                "asset_id": asset["id"], "filename": asset.get("filename"),
                "timestamp": round(timestamp, 2), "frame_number": frame_index, "duration": round(asset["duration"], 2)
            })
    return images, frame_map


def ask_director(assets: list[dict], transcripts: dict, frame_map: list[dict]) -> dict:
    schema = json.loads(Path("schemas/editing-blueprint.v1.schema.json").read_text())
    system_prompt = Path("prompts/universal-director.md").read_text()
    target = int(os.environ["TARGET_DURATION"])
    genre = os.environ.get("SELECTED_GENRE", "auto")
    instructions = os.environ.get("EDIT_INSTRUCTIONS", "").strip()
    compact_assets = [
        {"id": a["id"], "filename": a.get("filename"), "duration_seconds": round(a["duration"], 2)}
        for a in assets
    ]
    request_text = f"""
Create one complete editing blueprint. Return JSON only, matching this schema exactly:
{json.dumps(schema, separators=(',', ':'))}

Project ID: {os.environ['PROJECT_ID']}
Target duration: {target} seconds.
Preferred genre: {genre} (auto means infer from footage).
User instructions: {instructions or 'None'}.
Available clips: {json.dumps(compact_assets)}
Sampled frames, in the same order as the image attachments: {json.dumps(frame_map)}
Speech transcripts with source timestamps: {json.dumps(transcripts, ensure_ascii=False)}

Important:
- Use actual asset IDs from Available clips.
- CRITICAL: each uploaded file represents one complete scene. Return exactly one scene per uploaded file, in the exact upload order. Do not split a source file into multiple arbitrary scenes and do not reorder the four source scenes.
- Preserve each scene's meaningful action and dialogue; trim only genuine dead air or unusable handles. Scenes must cover the target timeline continuously and never exceed each source clip duration.
- For every scene after the first, deliberately choose transition_in from cut, fade, dissolve, whip, match_cut, or none based on actual visual movement and mood. Do not apply one identical transition everywhere.
- Captions and every audio_cues.at value use GLOBAL output timeline seconds, not source-clip or scene-local seconds. Only caption words that exist in transcripts; do not invent dialogue.
- Plan a sound bridge at suitable scene boundaries: natural ambience/audio continuation, whoosh timed to a visual transition, or a restrained impact for a reveal. Use only the renderer's original SFX asset IDs: vine_boom_style, bruh_drop, boing, record_scratch, whoosh, engine_rev, sad_trombone. Keep effects sparse and outside important dialogue. Set music_strategy to none because no licensed music track is bundled.
- Keep original spoken audio. Never add unsupported marketing claims.
- Aim for a strong 1–2 second opening hook and a coherent ending.
- The only allowed output is a single JSON object. Do not wrap it in Markdown.
"""
    content = [{"type": "text", "text": request_text}, *images_for_director]
    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt + "\nYou must obey the user-specific output schema supplied in the next message."},
            {"role": "user", "content": content}
        ],
        "temperature": 0.2,
        "max_tokens": 12000,
        "response_format": {"type": "json_object"}
    }
    def extract_json(response: dict) -> dict:
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError("The AI Director response contained no choices.")
        message = choices[0].get("message") or {}
        raw = message.get("content", "")
        if isinstance(raw, list):
            raw = "\\n".join(str(part.get("text", "")) for part in raw if isinstance(part, dict))
        if not isinstance(raw, str) or not raw.strip():
            raise RuntimeError("The AI Director returned an empty response.")
        decoder = json.JSONDecoder()
        # Accept a clean object or harmless prose/fences around one complete object.
        for index, char in enumerate(raw):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(raw[index:])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
        finish = choices[0].get("finish_reason", "unknown")
        raise ValueError(f"AI Director JSON parse failed (finish_reason={finish}, chars={len(raw)}). Preview: {raw[:500]!r}")

    last_error = None
    for attempt in range(2):
        try:
            response = api_json(BASE_URL + "/chat/completions", payload)
            return extract_json(response)
        except (ValueError, RuntimeError, KeyError, TypeError) as exc:
            last_error = exc
            if attempt == 0:
                print(f"AI Director returned malformed/incomplete JSON; retrying once with stricter output instructions. Detail: {exc}")
                retry_payload = dict(payload)
                retry_payload["max_tokens"] = 16000
                retry_payload["messages"] = list(payload["messages"]) + [{
                    "role": "user",
                    "content": "Your previous response was not valid complete JSON. Return ONLY one complete JSON object matching the supplied schema. Do not use Markdown, comments, trailing commas, or omit required fields. Ensure every string is properly escaped and all arrays/objects are closed."
                }]
                payload = retry_payload
    raise RuntimeError(f"AI Director failed after one retry: {last_error}")


def validate_blueprint(blueprint: dict, assets: list[dict], target: int) -> None:
    from jsonschema import validate
    schema = json.loads(Path("schemas/editing-blueprint.v1.schema.json").read_text())
    validate(blueprint, schema)
    valid_ids = {a["id"] for a in assets}
    scenes_in_order = sorted(blueprint["scenes"], key=lambda item: float(item["timeline_start"]))
    expected_order = [a["id"] for a in assets]
    actual_order = [scene["asset_id"] for scene in scenes_in_order]
    if actual_order != expected_order:
        raise ValueError("Each uploaded file is one scene: preserve the original upload order and use exactly one scene per source clip.")
    for scene in blueprint["scenes"]:
        if scene["asset_id"] not in valid_ids:
            raise ValueError("AI blueprint referenced an unknown source clip.")
        source = next(a for a in assets if a["id"] == scene["asset_id"])
        if scene["source_out"] <= scene["source_in"] or scene["source_out"] > source["duration"] + 0.1:
            raise ValueError("AI blueprint contains an invalid source time range.")
        if scene["timeline_end"] <= scene["timeline_start"]:
            raise ValueError("AI blueprint contains an invalid timeline range.")
    scenes = blueprint["scenes"]
    scenes.sort(key=lambda item: float(item["timeline_start"]))
    cursor = 0.0
    for scene in scenes:
        start = float(scene["timeline_start"])
        end = float(scene["timeline_end"])
        if abs(start - cursor) > 0.12:
            raise ValueError("AI blueprint contains a timeline gap or overlap; refusing a random-feeling assembly.")
        cursor = end
    if cursor < target * 0.85 or cursor > target + 1:
        raise ValueError("AI blueprint timeline does not match the requested output duration.")
    if len(scenes) > 18:
        raise ValueError("AI blueprint uses too many cuts; use fewer, more purposeful scenes.")


def ensure_sound_design(blueprint: dict) -> None:
    """Guarantee restrained original SFX when the AI omits usable cues."""
    scenes = sorted(blueprint["scenes"], key=lambda item: float(item["timeline_start"]))
    valid_ids = {"vine_boom_style", "bruh_drop", "boing", "record_scratch", "whoosh", "engine_rev", "sad_trombone"}
    existing = [cue for scene in scenes for cue in scene.get("audio_cues", [])
                if str(cue.get("asset_id") or "").lower() in valid_ids]
    if len(existing) >= 2:
        return
    genre = blueprint.get("classification", {}).get("primary_genre", "other")
    candidates = scenes[1:-1] if len(scenes) > 2 else scenes
    # Do not leave the soundtrack silent merely because the model omitted cues.
    wanted = min(4, max(2, round(len(scenes) / 3)))
    choices = (["boing", "record_scratch", "bruh_drop", "whoosh"]
               if genre in ("comedy", "two_character", "pov")
               else ["whoosh", "engine_rev", "vine_boom_style", "impact"])
    for index, scene in enumerate(candidates):
        if len(existing) >= wanted:
            break
        scene_start = float(scene.get("timeline_start", 0))
        scene_end = float(scene.get("timeline_end", scene_start + 1.0))
        at = scene_start + min(0.22, max(0.08, (scene_end - scene_start) * 0.12))
        if any(abs(float(c.get("at", -100)) - at) < 0.8 for item in scenes for c in item.get("audio_cues", [])):
            continue
        asset_id = choices[index % len(choices)]
        kind = "comedy" if asset_id in ("boing", "record_scratch", "bruh_drop") else ("engine" if asset_id == "engine_rev" else ("impact" if asset_id in ("vine_boom_style", "impact") else "whoosh"))
        scene.setdefault("audio_cues", []).append({"kind": kind, "asset_id": asset_id, "at": round(at, 2),
            "duration": 0.85, "gain_db": -5.5})
        existing.append(scene["audio_cues"][-1])
    # Every scene boundary gets a transition-specific whoosh unless the director already placed one.
    for index, scene in enumerate(scenes):
        if index == 0:
            continue
        transition = scene.get("transition_in", "cut")
        if transition in ("fade", "dissolve", "whip") and not any(
            str(c.get("kind", "")).lower() == "whoosh" and
            abs(float(c.get("at", -100)) - float(scene["timeline_start"])) < 0.7
            for item in scenes for c in item.get("audio_cues", [])
        ):
            scene.setdefault("audio_cues", []).append({
                "kind": "whoosh", "asset_id": "whoosh",
                "at": round(max(0.0, float(scene["timeline_start"]) - 0.12), 2),
                "duration": 0.55, "gain_db": -6.0
            })
    print(f"Sound design: {len([cue for item in scenes for cue in item.get('audio_cues', [])])} original SFX cues scheduled, including scene transitions.")


def make_srt(blueprint: dict) -> Path:
    entries = []
    for scene in blueprint["scenes"]:
        for caption in scene.get("captions", []):
            start = float(caption["start"])
            end = float(caption["end"])
            if end <= start:
                continue
            entries.append((start, end, caption["text"]))
    entries.sort(key=lambda x: x[0])
    def stamp(value: float) -> str:
        ms = int(max(0, value) * 1000)
        hours, ms = divmod(ms, 3600000)
        minutes, ms = divmod(ms, 60000)
        seconds, ms = divmod(ms, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"
    path = WORK / "captions.srt"
    path.write_text("\n\n".join(
        f"{i}\n{stamp(start)} --> {stamp(end)}\n{text}"
        for i, (start, end, text) in enumerate(entries, start=1)
    ), encoding="utf-8")
    return path



def generate_sound_library() -> dict[str, Path]:
    """Create original, royalty-free meme-style accents locally for this render."""
    library_dir = WORK / "sound-library"
    library_dir.mkdir(parents=True, exist_ok=True)
    sample_rate = 48000
    rng = random.Random(20261122)

    def write_sound(name: str, duration: float, synth) -> Path:
        path = library_dir / f"{name}.wav"
        frames = int(sample_rate * duration)
        with wave.open(str(path), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(sample_rate)
            data = bytearray()
            for i in range(frames):
                t = i / sample_rate
                value = max(-1.0, min(1.0, synth(t, duration)))
                data.extend(struct.pack("<h", int(value * 32767)))
            out.writeframes(data)
        return path

    def impact(t: float, d: float) -> float:
        env = math.exp(-5.2 * t)
        freq = 105 - 52 * min(1, t / d)
        return (math.sin(2 * math.pi * freq * t) * 0.78 + (rng.random() * 2 - 1) * 0.22) * env

    def whoosh(t: float, d: float) -> float:
        x = t / d
        env = max(0.0, math.sin(math.pi * x)) ** 1.7
        return (rng.random() * 2 - 1) * env * 0.58

    def boing(t: float, d: float) -> float:
        env = math.exp(-3.3 * t)
        phase = 2 * math.pi * (155 * t + 38 * (1 - math.exp(-7 * t)) / 7)
        return math.sin(phase) * env * 0.72

    def scratch(t: float, d: float) -> float:
        env = math.exp(-2.8 * t) * (0.45 + 0.55 * abs(math.sin(2 * math.pi * 8 * t)))
        tone = math.sin(2 * math.pi * (620 - 310 * t / d) * t)
        noise = rng.random() * 2 - 1
        return (tone * 0.55 + noise * 0.45) * env

    def engine(t: float, d: float) -> float:
        x = t / d
        freq = 75 + 190 * x
        phase = 2 * math.pi * (75 * t + 95 * t * t / d)
        return (2 / math.pi) * math.asin(math.sin(phase)) * (0.25 + 0.65 * x)

    def sad_tone(t: float, d: float) -> float:
        freq = 440 - 95 * (t / d)
        return math.sin(2 * math.pi * freq * t) * math.exp(-1.1 * t) * 0.55

    return {
        "impact": write_sound("impact", 1.05, impact),
        "whoosh": write_sound("whoosh", 0.85, whoosh),
        "boing": write_sound("boing", 1.15, boing),
        "scratch": write_sound("record-scratch", 0.9, scratch),
        "engine": write_sound("engine-rev", 1.35, engine),
        "sad": write_sound("sad-trombone-style", 1.6, sad_tone),
    }


def resolve_sound_cue(cue: dict, library: dict[str, Path]) -> Path | None:
    if cue.get("kind") in ("music", "voiceover", "silence"):
        return None
    requested = str(cue.get("asset_id") or "").lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "vine_boom": "impact", "vine_boom_style": "impact", "bruh": "impact",
        "bruh_drop": "impact", "impact": "impact", "dramatic_hit": "impact",
        "whoosh": "whoosh", "swoosh": "whoosh", "transition_whoosh": "whoosh",
        "boing": "boing", "cartoon_boing": "boing", "comedy": "boing",
        "record_scratch": "scratch", "scratch": "scratch",
        "engine": "engine", "engine_rev": "engine",
        "sad_violin": "sad", "sad_trombone": "sad",
    }
    key = aliases.get(requested)
    if key is None:
        key = {"whoosh": "whoosh", "impact": "impact", "comedy": "boing",
               "engine": "engine", "ambience": "whoosh"}.get(cue.get("kind"))
    return library.get(key) if key else None


def build_audio_mix(blueprint: dict, source_video: Path, output: Path, subtitle_filter: str) -> None:
    """Mix source dialogue with timestamped, dialogue-ducked original SFX."""
    library = generate_sound_library()
    ensure_sound_design(blueprint)
    cues = []
    for scene in blueprint["scenes"]:
        for cue in scene.get("audio_cues", []):
            sound = resolve_sound_cue(cue, library)
            if sound is None:
                continue
            at = max(0.0, float(cue.get("at", scene.get("timeline_start", 0))))
            if at >= float(blueprint["output"]["duration_seconds"]):
                continue
            duration = max(0.12, min(float(cue.get("duration", 1.0)), 2.0))
            gain_db = min(-3.0, max(-12.0, float(cue.get("gain_db", -5.5))))
            cues.append((sound, at, duration, gain_db))
    cues = sorted(cues, key=lambda item: item[1])[:14]

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source_video)]
    for sound, _, _, _ in cues:
        cmd += ["-i", str(sound)]

    if cues:
        filters = []
        mix_labels = ["[0:a]"]
        for index, (_, at, duration, gain_db) in enumerate(cues, start=1):
            delay_ms = int(at * 1000)
            label = f"sfx{index}"
            ducked = f"duck{index}"
            volume = 10 ** (gain_db / 20)
            filters.append(
                f"[{index}:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
                f"volume={volume:.5f},adelay={delay_ms}|{delay_ms}[{label}]"
            )
            filters.append(
                f"[{label}][0:a]sidechaincompress=threshold=0.12:ratio=2.2:"
                f"attack=8:release=180[{ducked}]"
            )
            mix_labels.append(f"[{ducked}]")
        filters.append(
            "".join(mix_labels) + f"amix=inputs={len(mix_labels)}:duration=first:"
            "dropout_transition=0:normalize=0,alimiter=limit=0.89,"
            "loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
        )
        cmd += ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[aout]"]
        print(f"Sound design: mixed {len(cues)} timestamped SFX cues with dialogue ducking.")
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]

    cmd += [
        "-vf", subtitle_filter + ":force_style='FontName=Arial,FontSize=18,Bold=1,Outline=3,Shadow=1,Alignment=2,MarginV=250,BorderStyle=1,Spacing=0.2'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-c:a", "aac", "-b:a", "160k", "-t", str(blueprint["output"]["duration_seconds"]),
        "-movflags", "+faststart", str(output)
    ]
    run(cmd)


def render(blueprint: dict, assets: list[dict]) -> None:
    asset_map = {a["id"]: a for a in assets}
    normalized = []
    transition_seconds = min(0.26, 0.85 / max(1, len(blueprint["scenes"]) - 1))
    transition_seconds = max(0.08, transition_seconds)
    transition_map = {
        "fade": "fade", "dissolve": "dissolve",
        "whip": "smoothleft", "cut": "fade",
        "match_cut": "fade", "none": "fade"
    }
    for index, scene in enumerate(blueprint["scenes"], start=1):
        asset = asset_map[scene["asset_id"]]
        source_duration = float(scene["source_out"]) - float(scene["source_in"])
        timeline_duration = float(scene["timeline_end"]) - float(scene["timeline_start"])
        if source_duration <= 0 or timeline_duration <= 0:
            raise ValueError("Scene duration must be positive.")
        speed = source_duration / timeline_duration
        if not 0.5 <= speed <= 2:
            raise ValueError("A selected scene requires an unsupported speed change.")
        profile = scene["visual_profile"]
        color = {
            "cinematic_warm": "eq=saturation=1.08:contrast=1.04,colorbalance=rs=0.04:gs=0.01",
            "cinematic_cool": "eq=saturation=0.96:contrast=1.05,colorbalance=bs=0.04:gs=0.01",
            "dramatic": "eq=contrast=1.12:saturation=0.90:brightness=-0.01",
            "clean_social": "eq=contrast=1.03:saturation=1.04",
            "natural": "eq=contrast=1.01:saturation=1.02",
            "neutral": "null"
        }.get(profile, "null")
        # Consistent, restrained premium grade on every scene; AI profile adds a small mood adjustment.
        base_grade = "eq=contrast=1.07:saturation=1.06:gamma=1.02:brightness=0.004,curves=all='0/0.015 0.25/0.23 0.75/0.79 1/0.985',colorbalance=rs=0.012:gs=0.004:bs=-0.008"
        # Subtle, continuous camera push-in creates real motion on otherwise static shots.
        motion = "zoompan=z='min(zoom+0.00032,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
        video_filters = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,{base_grade},{color},{motion},vignette=PI/5,unsharp=5:5:0.35:3:3:0.0,setpts=PTS/{speed:.6f},format=yuv420p"
        part = WORK / f"scene-{index:02d}.mp4"
        has_audio = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
            "stream=index", "-of", "csv=p=0", asset["path"]
        ], capture_output=True, text=True).stdout.strip()
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(scene["source_in"]), "-i", asset["path"]]
        if has_audio:
            cmd += ["-t", str(source_duration), "-vf", video_filters, "-af", f"atempo={speed:.6f},aresample=48000"]
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k"]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-t", str(source_duration),
                    "-map", "0:v:0", "-map", "1:a:0", "-vf", video_filters,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k"]
        if scene.get("transition_in") in ("fade", "dissolve"):
            cmd += ["-vf", video_filters + ",fade=t=in:st=0:d=0.22"]
        cmd += ["-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(part)]
        run(cmd)
        normalized.append(part)

    # Blend adjacent scenes with matching video and audio transitions instead of a raw file concat.
    if len(normalized) == 1:
        joined = normalized[0]
        adjusted = json.loads(json.dumps(blueprint))
    else:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        for part in normalized:
            cmd += ["-i", str(part)]
        filters = []
        first_duration = float(blueprint["scenes"][0]["timeline_end"]) - float(blueprint["scenes"][0]["timeline_start"])
        # Re-normalize AFTER speed changes: xfade requires identical CFR, size,
        # pixel format and timebase on every input, even for variable-rate phone clips.
        filters.append("[0:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v0]")
        filters.append("[0:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a0]")
        composite_duration = first_duration
        actual_starts = [0.0]
        for index in range(1, len(normalized)):
            scene = blueprint["scenes"][index]
            duration = float(scene["timeline_end"]) - float(scene["timeline_start"])
            trans = transition_seconds
            transition_name = transition_map.get(scene.get("transition_in", "cut"), "fade")
            offset = max(0.0, composite_duration - trans)
            filters.append(
                f"[{index}:v]fps=30,scale=1080:1920,setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{index}]"
            )
            filters.append(
                f"[{index}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{index}]"
            )
            filters.append(
                f"[v{index-1}][v{index}]xfade=transition={transition_name}:duration={trans:.3f}:offset={offset:.3f}[vx{index}]"
            )
            filters.append(
                f"[a{index-1}][a{index}]acrossfade=d={trans:.3f}:c1=tri:c2=tri[ax{index}]"
            )
            actual_starts.append(offset)
            composite_duration = composite_duration + duration - trans
        last = len(normalized) - 1
        joined = WORK / "joined.mp4"
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[vx{last}]", "-map", f"[ax{last}]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(joined)]
        run(cmd)
        adjusted = json.loads(json.dumps(blueprint))
        for index, scene in enumerate(adjusted["scenes"]):
            shift = actual_starts[index] - float(scene["timeline_start"])
            scene["timeline_start"] = actual_starts[index]
            scene["timeline_end"] = actual_starts[index] + (
                float(blueprint["scenes"][index]["timeline_end"]) -
                float(blueprint["scenes"][index]["timeline_start"])
            )
            for caption in scene.get("captions", []):
                caption["start"] = max(0.0, float(caption["start"]) + shift)
                caption["end"] = max(caption["start"] + 0.05, float(caption["end"]) + shift)
            for cue in scene.get("audio_cues", []):
                cue["at"] = max(0.0, float(cue["at"]) + shift)
    captions = make_srt(adjusted)
    subtitle_filter = "subtitles=" + str(captions.resolve()).replace("\\", "/").replace(":", "\\:")
    build_audio_mix(adjusted, joined, OUTPUT, subtitle_filter)


def upload_output() -> None:
    params = urllib.parse.urlencode({
        "job_id": os.environ["JOB_ID"], "user_id": os.environ["USER_ID"],
        "expires": os.environ["JOB_EXPIRES"], "signature": os.environ["JOB_SIGNATURE"], "run_id": os.environ["GITHUB_RUN_ID"]
    })
    data = OUTPUT.read_bytes()
    request = urllib.request.Request(
        os.environ["OUTPUT_UPLOAD_BASE_URL"] + "?" + params, data=data,
        headers={"Content-Type": "video/mp4", "Content-Length": str(len(data)), "Authorization": "Bearer " + os.environ["OIDC_TOKEN"], "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
            if not result.get("success"):
                raise RuntimeError("Cloud storage did not confirm the rendered file.")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Could not save rendered video to Cloudflare R2 (HTTP {error.code}).") from None


def main() -> None:
    if not API_KEY:
        raise RuntimeError("RELINK_API_KEY repository secret is missing.")
    WORK.mkdir(exist_ok=True)
    load_manifest()
    assets = download_assets()
    print("Transcribing dialogue with local Whisper small model and word timestamps...")
    transcripts = transcribe(assets)
    global images_for_director
    images_for_director, frame_map = sample_frames(assets)
    print(f"Sending {len(frame_map)} dense visual samples and improved transcripts to AI Director ({VISION_MODEL})...")
    blueprint = ask_director(assets, transcripts, frame_map)
    validate_blueprint(blueprint, assets, int(os.environ["TARGET_DURATION"]))
    ensure_sound_design(blueprint)
    Path("editing-blueprint.json").write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    print("AI Director plan validated. Rendering...")
    render(blueprint, assets)
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height", "-of", "json", str(OUTPUT)]))
    video_stream = next((s for s in probe.get("streams", []) if s.get("codec_name") == "h264"), None)
    if not video_stream or video_stream.get("width") != 1080 or video_stream.get("height") != 1920:
        raise RuntimeError("Final quality check failed: output is not 1080x1920 H.264.")
    actual_duration = float(probe.get("format", {}).get("duration", 0))
    if not int(os.environ["TARGET_DURATION"]) - 1 <= actual_duration <= int(os.environ["TARGET_DURATION"]) + 1:
        raise RuntimeError("Final quality check failed: output duration is outside tolerance.")
    upload_output()
    print(f"SUCCESS: rendered {actual_duration:.1f}s vertical video ({probe['format'].get('size')} bytes).")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"AI EDIT FAILED: {error}", file=sys.stderr)
        sys.exit(1)
