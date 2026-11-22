#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error

raw_manifest = os.environ.get("MANIFEST_JSON", "").strip()
try:
    manifest = json.loads(raw_manifest) if raw_manifest else None
except json.JSONDecodeError:
    manifest = None
if not manifest or manifest.get("jobId") != os.environ.get("JOB_ID"):
    print("Could not read the signed manifest from workflow inputs; failure status was not reported.")
    raise SystemExit(0)

params = urllib.parse.urlencode({
    "job_id": manifest["jobId"], "user_id": manifest["userId"],
    "expires": manifest["expires"], "signature": manifest["signature"]
})
request = urllib.request.Request(
    os.environ["FAILURE_REPORT_URL"] + "?" + params,
    data=json.dumps({"message": "AI editing gagal pada tahap analisis, transkripsi, atau rendering. Buka GitHub Actions untuk detail teknis."}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        print("Failure status reported to the dashboard.")
except Exception as error:
    print("Could not report failure to dashboard:", type(error).__name__)
