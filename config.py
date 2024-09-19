from urllib.parse import urlencode
from client import CLIENT_ID, CLIENT_SECRET # Delete or comment this line

params = {
    # Override both client params with yours
    # (go to https://developer.spotify.com/dashboard if you don't have a spotify dev account)
    'CLIENT_ID': CLIENT_ID,
    'CLIENT_SECRET': CLIENT_SECRET,
    'SCOPE': 'user-read-playback-state'
}

urls = {
    'REDIRECT_URI': 'http://localhost:8888/callback',
    'AUTH_URL': f"https://accounts.spotify.com/authorize?{urlencode({'client_id': params['CLIENT_ID'], 'response_type': 'code', 'redirect_uri': 'http://localhost:8888/callback', 'scope': params['SCOPE']})}",
    'TOKEN_URL': 'https://accounts.spotify.com/api/token'
}
