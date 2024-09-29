from urllib.parse import urlencode
from utils.utils import load_json

# You can delete or comment this line, or create a client.json in config dir, then add your spotify client data there
client_data = load_json(r"config\client.json")

params = {
  # Override both client params with yours
  # (go to https://developer.spotify.com/dashboard if you don't have a spotify dev account)
  "CLIENT_ID": client_data.get("CLIENT_ID", None),
  "CLIENT_SECRET": client_data.get("CLIENT_SECRET", None),
  "SCOPE": "user-read-playback-state",
}

urls = {
  "REDIRECT_URI": "http://localhost:8888/callback",
  "AUTH_URL": f"https://accounts.spotify.com/authorize?{urlencode({ 'client_id': params['CLIENT_ID'], 'response_type': 'code', 'redirect_uri': 'http://localhost:8888/callback', 'scope': params['SCOPE'] })}",
  "TOKEN_URL": "https://accounts.spotify.com/api/token",
}
