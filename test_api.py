
import json
import urllib.error
import urllib.request
from pathlib import Path

TOKEN_DIR = Path.home() / ".together_spotify"

ENDPOINTS = {
    "currently playing": "/me/player/currently-playing",
    "recently played": "/me/player/recently-played?limit=3",
}

for account in ("me", "girlfriend"):
    print(f"\n=== {account} ===")
    token_file = TOKEN_DIR / f"{account}.json"

    with token_file.open() as f:
        token = json.load(f)["access_token"]

    for label, endpoint in ENDPOINTS.items():
        req = urllib.request.Request(
            "https://api.spotify.com/v1" + endpoint,
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.load(response)
                if label == "currently playing":
                    item = data.get("item") or {}
                    artists = ", ".join(
                        a["name"] for a in item.get("artists", [])
                    )
                    print(f"{label}: {item.get('name', 'Unknown')} — {artists}")
                else:
                    items = data.get("items", [])
                    print(f"{label}: {len(items)} recent items returned")
        except urllib.error.HTTPError as e:
            if e.code == 204:
                print(f"{label}: nothing currently playing (normal)")
            else:
                print(f"{label}: HTTP {e.code}")
        except Exception as e:
            print(f"{label}: {type(e).__name__}: {e}")
