#!/usr/bin/env python3
"""Cloud AI director: inspect footage, transcribe speech, plan and render a vertical edit."""
from __future__ import annotations

import base64
import json
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
VISION_MODEL = os.environ.get("RELINK_VISION_MODEL", "deepseek-flash")


def run(command: list[str], *, capture: bool = True) -> str:
    result = subprocess.run(command, check=True, text=True, capture_output=capture)
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
        query = urllib.parse.urlencode({**params, "key": asset["key"]})
        url = base + "?" + query
        path = WORK / f"source-{index:02d}.mov"
        request = urllib.request.Request(url, headers={"User-Agent": "AI-Video-Factory-Runner/1"})
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
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    transcripts: dict[str, list[dict]] = {}
    for asset in assets:
        audio = WORK / (Path(asset["path"]).stem + ".wav")
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", asset["path"],
            "-vn", "-ac", "1", "-ar", "16000", str(audio)
        ], check=True, capture_output=True)
        audio_probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", asset["path"]], capture_output=True, text=True).stdout.strip()
        if not audio_probe:
            transcripts[asset["id"]] = []
            continue
        segments, _ = model.transcribe(str(audio), vad_filter=True, beam_size=1)
        transcripts[asset["id"]] = [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments if s.text.strip()
        ]
    return transcripts


def sample_frames(assets: list[dict]) -> tuple[list[dict], list[dict]]:
    images: list[dict] = []
    frame_map: list[dict] = []
    for asset in assets:
        for fraction in (0.2, 0.5, 0.8):
            timestamp = max(0.05, min(asset["duration"] - 0.05, asset["duration"] * fraction))
            image_path = WORK / f"{asset['id'][:8]}-{int(fraction * 100)}.jpg"
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(timestamp),
                "-i", asset["path"], "-frames:v", "1", "-vf", "scale=640:-2",
                "-q:v", "6", str(image_path)
            ], check=True, capture_output=True)
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            images.append({
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64," + encoded, "detail": "low"}
            })
            frame_map.append({
                "asset_id": asset["id"], "filename": asset.get("filename"),
                "timestamp": round(timestamp, 2), "duration": round(asset["duration"], 2)
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
- Scenes must be ordered, cover the target timeline from 0 to approximately {target} seconds, and never exceed each source clip duration.
- Captions use GLOBAL timeline seconds, not source clip seconds. Only caption words that exist in transcripts; do not invent dialogue.
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
    response = api_json(BASE_URL + "/chat/completions", payload)
    choices = response.get("choices") or []
    raw = (choices[0].get("message") or {}).get("content", "") if choices else ""
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("The AI Director returned an empty response.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise RuntimeError("The AI Director did not return valid JSON.")
        return json.loads(match.group(0))


def validate_blueprint(blueprint: dict, assets: list[dict], target: int) -> None:
    from jsonschema import validate
    schema = json.loads(Path("schemas/editing-blueprint.v1.schema.json").read_text())
    validate(blueprint, schema)
    valid_ids = {a["id"] for a in assets}
    for scene in blueprint["scenes"]:
        if scene["asset_id"] not in valid_ids:
            raise ValueError("AI blueprint referenced an unknown source clip.")
        source = next(a for a in assets if a["id"] == scene["asset_id"])
        if scene["source_out"] <= scene["source_in"] or scene["source_out"] > source["duration"] + 0.1:
            raise ValueError("AI blueprint contains an invalid source time range.")
        if scene["timeline_end"] <= scene["timeline_start"]:
            raise ValueError("AI blueprint contains an invalid timeline range.")
    last = max(scene["timeline_end"] for scene in blueprint["scenes"])
    if last < target * 0.85 or last > target + 1:
        raise ValueError("AI blueprint timeline does not match the requested output duration.")


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


def render(blueprint: dict, assets: list[dict]) -> None:
    asset_map = {a["id"]: a for a in assets}
    normalized = []
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
        video_filters = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,{color},setpts=PTS/{speed:.6f},format=yuv420p"
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

    concat_file = WORK / "concat.txt"
    concat_file.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in normalized), encoding="utf-8")
    silent_concat = WORK / "joined.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent_concat)])
    captions = make_srt(blueprint)
    subtitle_filter = "subtitles=" + str(captions.resolve()).replace("\\", "/").replace(":", "\\:")
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(silent_concat),
        "-vf", subtitle_filter + ":force_style='FontName=Arial,FontSize=19,Outline=2,Shadow=1,Alignment=2,MarginV=135'",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k",
        "-t", str(blueprint["output"]["duration_seconds"]), "-movflags", "+faststart", str(OUTPUT)
    ])


def upload_output() -> None:
    params = urllib.parse.urlencode({
        "job_id": os.environ["JOB_ID"], "user_id": os.environ["USER_ID"],
        "expires": os.environ["JOB_EXPIRES"], "signature": os.environ["JOB_SIGNATURE"]
    })
    data = OUTPUT.read_bytes()
    request = urllib.request.Request(
        os.environ["OUTPUT_UPLOAD_BASE_URL"] + "?" + params, data=data,
        headers={"Content-Type": "video/mp4", "Content-Length": str(len(data))},
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
    assets = download_assets()
    print("Transcribing dialogue with local Whisper tiny model...")
    transcripts = transcribe(assets)
    global images_for_director
    images_for_director, frame_map = sample_frames(assets)
    print(f"Sending {len(frame_map)} keyframes and transcripts to AI Director ({VISION_MODEL})...")
    blueprint = ask_director(assets, transcripts, frame_map)
    validate_blueprint(blueprint, assets, int(os.environ["TARGET_DURATION"]))
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
