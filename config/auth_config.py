import spotipy
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlencode
from utils.helpers import load_json
from config.base import ConfigRelatedMeta

class SpotifyAuthConfig(metaclass=ConfigRelatedMeta):
  def __init__(self):
    self.SP: spotipy.Spotify = self.get_spotify_client()

    #  You must create a client.json in config dir, then add your spotify client data there
    self.CLIENT_DATA: dict[str, str] = load_json(r"config\client.json")
    self.PARAMS: dict[str, str] = {
      # Override both client params with yours
      # (go to https://developer.spotify.com/dashboard if you don't have a spotify dev account)
      "CLIENT_ID": self.CLIENT_DATA.get("CLIENT_ID", None),
      "CLIENT_SECRET": self.CLIENT_DATA.get("CLIENT_SECRET", None),
      # "SCOPE": "user-read-playback-state user-read-currently-playing", # If you don't want to control playback through the app comment the line below and use this one
      "SCOPE": "user-read-playback-state user-modify-playback-state user-read-currently-playing",  # Modify permission if you want to control playback through the app
    }
    self.URLS: dict[str, str] = {
      "REDIRECT_URI": "http://localhost:8888/callback",
      "AUTH_URL": f"https://accounts.spotify.com/authorize?{urlencode({ 'client_id': self.PARAMS['CLIENT_ID'], 'response_type': 'code', 'redirect_uri': 'http://localhost:8888/callback', 'scope': self.PARAMS['SCOPE'] })}",
      "TOKEN_URL": "https://accounts.spotify.com/api/token",
    }

  def get_spotify_client(self) -> spotipy.Spotify:
    return spotipy.Spotify(
      auth_manager=SpotifyOAuth(
        client_id=self.PARAMS["CLIENT_ID"],
        client_secret=self.PARAMS["CLIENT_SECRET"],
        redirect_uri=self.URLS["REDIRECT_URI"],
        scope=self.PARAMS["SCOPE"],
      )
    )

# singleton instance
sp_auth: SpotifyAuthConfig = SpotifyAuthConfig()
