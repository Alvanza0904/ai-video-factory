#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error

manifest_query = urllib.parse.urlencode({"job_id": os.environ["JOB_ID"], "run_id": os.environ["GITHUB_RUN_ID"]})
manifest_request = urllib.request.Request(
    os.environ["MANIFEST_URL"] + "?" + manifest_query,
    headers={"Authorization": "Bearer " + os.environ["OIDC_TOKEN"], "Accept": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"}
)
try:
    with urllib.request.urlopen(manifest_request, timeout=30) as response:
        manifest = json.loads(response.read().decode())
except urllib.error.HTTPError as error:
    detail = error.read().decode("utf-8", errors="replace")[:1200]
    print("Could not load job manifest for failure report:", error.code, dict(error.headers), detail)
    raise SystemExit(0)
except Exception as error:
    print("Could not load job manifest for failure report:", type(error).__name__, str(error))
    raise SystemExit(0)

params = urllib.parse.urlencode({
    "job_id": manifest["jobId"], "user_id": manifest["userId"],
    "expires": manifest["expires"], "signature": manifest["signature"], "run_id": os.environ["GITHUB_RUN_ID"]
})
request = urllib.request.Request(
    os.environ["FAILURE_REPORT_URL"] + "?" + params,
    data=json.dumps({"message": "AI editing gagal pada tahap analisis, transkripsi, atau rendering. Buka GitHub Actions untuk detail teknis."}).encode(),
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["OIDC_TOKEN"], "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"},
    method="POST"
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        print("Failure status reported to the dashboard.")
except Exception as error:
    print("Could not report failure to dashboard:", type(error).__name__)
