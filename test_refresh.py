
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

folder = Path.home() / ".together_spotify"
client_id = input("Spotify Client ID: ").strip()

for account in ("me", "girlfriend"):
    path = folder / f"{account}.json"
    data = json.loads(path.read_text())
    refresh_token = data.get("refresh_token")

    print(f"\n{account}: ", end="")

    if not refresh_token:
        print("No refresh token")
        continue

    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()

    request = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            updated = json.load(response)

        data["access_token"] = updated["access_token"]
        data["expires_in"] = updated.get("expires_in", data.get("expires_in"))
        data["scope"] = updated.get("scope", data.get("scope"))

        # Keep the previous refresh token if Spotify doesn't return a new one.
        if updated.get("refresh_token"):
            data["refresh_token"] = updated["refresh_token"]

        temp_path = path.with_suffix(".tmp")
        with temp_path.open("w") as f:
            json.dump(data, f, indent=2)
        os.chmod(temp_path, 0o600)
        temp_path.replace(path)

        print("Refresh succeeded; token file updated.")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}. Check the Client ID and refresh token.")
