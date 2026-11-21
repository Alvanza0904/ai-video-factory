#!/usr/bin/env python3
"""Minimal Re:Link Gateway connection smoke test. Never prints credentials."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("RELINK_BASE_URL", "https://api.relink-gateway.biz.id/v1").rstrip("/")
MODEL = os.environ.get("RELINK_MODEL", "deepseek-v4-pro")
API_KEY = os.environ.get("RELINK_API_KEY", "")


def main() -> None:
    if not API_KEY:
        raise RuntimeError("Missing RELINK_API_KEY repository secret.")
    if not BASE_URL.startswith("https://"):
        raise RuntimeError("RELINK_BASE_URL must use HTTPS.")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a connection test. Reply with exactly: RELINK_OK"
            },
            {"role": "user", "content": "Connection test. Reply exactly as instructed."}
        ],
        "temperature": 0,
        "max_tokens": 16
    }
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # Do not print response bodies: gateways may echo sensitive request metadata.
        raise RuntimeError(f"Re:Link returned HTTP {error.code}. Check key, model access, and token balance.") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach Re:Link Gateway: {error.reason}") from None

    choices = body.get("choices") or []
    content = (choices[0].get("message") or {}).get("content", "") if choices else ""
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Re:Link responded, but no text completion was returned.")
    print(f"Re:Link connection successful. Model: {MODEL}.")
    print(f"Model response: {content.strip()[:120]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RELINK CHECK FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
