#!/usr/bin/env python3
"""Read the model catalog endpoint only; this does not submit an inference request."""
import json
import os
import urllib.request
import urllib.error

key = os.environ.get("RELINK_API_KEY", "")
base = os.environ.get("RELINK_BASE_URL", "https://api.relink-gateway.biz.id/v1").rstrip("/")
if not key:
    raise SystemExit("RELINK_API_KEY repository secret is missing.")
request = urllib.request.Request(base + "/models",
    headers={"Authorization": "Bearer " + key, "Accept": "application/json"},
    method="GET")
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as error:
    raise SystemExit(f"Model catalog request failed: HTTP {error.code}. No inference request was sent.") from None
except urllib.error.URLError as error:
    raise SystemExit(f"Cannot reach Re:Link model catalog: {error.reason}") from None

models = data.get("data", []) if isinstance(data, dict) else []
if not isinstance(models, list):
    raise SystemExit("Unexpected model catalog response.")
ids = sorted({str(item.get("id")) for item in models if isinstance(item, dict) and item.get("id")})
if not ids:
    print("The gateway returned no model IDs in the standard OpenAI /models format.")
    print("Top-level fields:", ", ".join(sorted(data.keys())) if isinstance(data, dict) else type(data).__name__)
else:
    print("Models listed by the connected Re:Link gateway (catalog only; no inference billed):")
    for model_id in ids:
        print("- " + model_id)
