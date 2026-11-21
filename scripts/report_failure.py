#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request

params = urllib.parse.urlencode({
    "job_id": os.environ["JOB_ID"],
    "user_id": os.environ["USER_ID"],
    "expires": os.environ["JOB_EXPIRES"],
    "signature": os.environ["JOB_SIGNATURE"]
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
