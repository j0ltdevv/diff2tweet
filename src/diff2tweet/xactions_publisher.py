from __future__ import annotations
import subprocess
import json
import os

def post_via_xactions(text: str) -> str:
    # Nécessite: npm install -g xactions + xactions login --from-browser
    # ou env XACTIONS_SESSION_COOKIE
    env = os.environ.copy()
    # XActions lit le cookie depuis --cookies-file ou XACTIONS_SESSION_COOKIE
    result = subprocess.run(
        ["npx", "xactions", "post", "--text", text, "--json"],
        capture_output=True, text=True, env=env, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"xactions failed: {result.stderr or result.stdout}")
    try:
        data = json.loads(result.stdout)
        return str(data.get("id") or data.get("tweetId") or "ok")
    except:
        return result.stdout.strip()[:100]
