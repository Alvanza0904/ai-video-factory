#!/usr/bin/env python3
import base64, json, os, urllib.request, urllib.error

key = os.environ.get("RELINK_API_KEY", "")
base = os.environ.get("RELINK_BASE_URL", "https://api.relink-gateway.biz.id/v1").rstrip("/")
model = os.environ.get("RELINK_VISION_MODEL", "deepseek-flash")
if not key:
    raise SystemExit("RELINK_API_KEY missing")

# 1x1 PNG, used only to confirm image-input support at the configured gateway.
png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/X7sAAAAASUVORK5CYII=")
payload = {
    "model": model,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "This is a vision API test. Describe the image in one short sentence."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode(), "detail": "low"}}
        ]
    }],
    "max_tokens": 80
}
request = urllib.request.Request(base + "/chat/completions", data=json.dumps(payload).encode(),
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode())
except urllib.error.HTTPError as error:
    raise SystemExit(f"Vision model check failed: HTTP {error.code}. Gateway/model may not support image input.") from None
choices = data.get("choices") or []
answer = (choices[0].get("message") or {}).get("content", "") if choices else ""
if not isinstance(answer, str) or not answer.strip():
    raise SystemExit("Vision model returned no text.")
print("Vision API is reachable via Re:Link. Model:", model)
print("Image response:", answer[:160])
