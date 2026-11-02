
import base64
import hashlib
import json
import os
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CLIENT_ID = "eca9189f55f7440e9b4bc14dea5fe61c"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-read-recently-played",
]

label = input("Save this authorization as (me / girlfriend): ").strip().lower()
if label not in {"me", "girlfriend"}:
    raise SystemExit("Enter either 'me' or 'girlfriend'.")

if CLIENT_ID == "PASTE_YOUR_CLIENT_ID_HERE":
    raise SystemExit("Edit authorize.py and insert your Client ID first.")

verifier = secrets.token_urlsafe(64)
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()
).decode().rstrip("=")
state = secrets.token_urlsafe(24)

result = {}
finished = threading.Event()


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(
            urllib.parse.urlparse(self.path).query
        )

        if params.get("state", [None])[0] != state:
            self.send_error(400, "State mismatch")
            result["error"] = "OAuth state mismatch"
            finished.set()
            return

        if "error" in params:
            result["error"] = params["error"][0]
        elif "code" in params:
            result["code"] = params["code"][0]
        else:
            result["error"] = "Missing authorization code"

        body = (
            b"Authorization received. You can close this browser tab "
            b"and return to Terminal."
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        finished.set()

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 8888), CallbackHandler)
server.timeout = 180

params = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": " ".join(SCOPES),
    "state": state,
    "code_challenge_method": "S256",
    "code_challenge": challenge,
}

url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)

print(f"Starting authorization for: {label}")
print("Your browser will open. Sign in to the correct Spotify account.")
webbrowser.open(url)

while not finished.is_set():
    server.handle_request()

server.server_close()

if "error" in result:
    raise SystemExit(f"Authorization failed: {result['error']}")

payload = urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "grant_type": "authorization_code",
    "code": result["code"],
    "redirect_uri": REDIRECT_URI,
    "code_verifier": verifier,
}).encode()

request = urllib.request.Request(
    "https://accounts.spotify.com/api/token",
    data=payload,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

with urllib.request.urlopen(request, timeout=30) as response:
    tokens = json.load(response)

if "access_token" not in tokens:
    raise SystemExit(f"Token exchange failed: {tokens}")

folder = Path.home() / ".together_spotify"
folder.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(folder, 0o700)

output = folder / f"{label}.json"
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as file:
    json.dump(tokens, file, indent=2)

print(f"Success! Tokens saved privately to {output}")
print("Keep this file private. Do not commit it to Git.")

