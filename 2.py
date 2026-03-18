#!/usr/bin/env python3
import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request

URL = "https://b12.io/apply/submission"
SIGNING_SECRET = os.getenv("B12_SIGNING_SECRET", "hello-there-from-b12").encode("utf-8")

# Put your real values here (or provide env vars listed below).
USER_CONFIG = {
    "name": "Michael Zhang",
    "email": "michael.zhang73@outlook.com",
    "resume_link": "https://drive.google.com/file/d/1SizIELaIiRTT_Jl53YQdhh8K0QyOYTFN/view?usp=drive_link",
    "repository_link": "https://github.com/michaelzhang73",
    "action_run_link": "https://github.com/michaelzhang73/bittensor_fun/actions/runs/23268530206",
}


def iso8601_utc_now() -> str:
    # Example format: 2026-01-06T16:59:37.571Z
    now = dt.datetime.now(dt.timezone.utc)
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> int:
    # Fill from env vars first; otherwise fall back to USER_CONFIG above.
    payload = {
        "action_run_link": os.getenv(
            "ACTION_RUN_LINK",
            USER_CONFIG["action_run_link"],
        ),
        "email": os.getenv("APPLY_EMAIL", USER_CONFIG["email"]),
        "name": os.getenv("APPLY_NAME", USER_CONFIG["name"]),
        "repository_link": os.getenv(
            "REPOSITORY_LINK",
            USER_CONFIG["repository_link"],
        ),
        "resume_link": os.getenv("RESUME_LINK", USER_CONFIG["resume_link"]),
        "timestamp": iso8601_utc_now(),
    }

    # Canonical JSON: sorted keys, compact separators, UTF-8.
    body_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    body_bytes = body_str.encode("utf-8")

    digest = hmac.new(SIGNING_SECRET, body_bytes, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Signature-256": f"sha256={digest}",
    }

    req = urllib.request.Request(URL, data=body_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            if resp.status != 200:
                print(f"Unexpected status: {resp.status}\n{resp_body}", file=sys.stderr)
                return 1
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP error: {e.code}\n{err}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    try:
        result = json.loads(resp_body)
    except json.JSONDecodeError:
        print(f"Non-JSON response: {resp_body}", file=sys.stderr)
        return 1

    if result.get("success") is True and "receipt" in result:
        # Print this in CI logs.
        print(result["receipt"])
        return 0

    print(f"Unexpected response: {result}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
