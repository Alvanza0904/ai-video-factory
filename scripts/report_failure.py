#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error

manifest_query = urllib.parse.urlencode({"job_id": os.environ["JOB_ID"], "run_id": os.environ["GITHUB_RUN_ID"]})
manifest_request = urllib.request.Request(
    os.environ["MANIFEST_URL"] + "?" + manifest_query,
    headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Accept": "application/json"}
)
try:
    with urllib.request.urlopen(manifest_request, timeout=30) as response:
        manifest = json.loads(response.read().decode())
except Exception as error:
    print("Could not load job manifest for failure report:", type(error).__name__)
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
