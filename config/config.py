import darkdetect
import spotipy, os
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlencode
from utils.helpers import load_json

# You can delete or comment this line, or create a client.json in config dir, then add your spotify client data there
CLIENT_DATA = load_json(r"config\client.json")

PARAMS = {
  # Override both client params with yours
  # (go to https://developer.spotify.com/dashboard if you don't have a spotify dev account)
  "CLIENT_ID": CLIENT_DATA.get("CLIENT_ID", None),
  "CLIENT_SECRET": CLIENT_DATA.get("CLIENT_SECRET", None),
  # "SCOPE": "user-read-playback-state", # If you don't want to control playback through the app comment the line below and use this one
  "SCOPE": "user-read-playback-state user-modify-playback-state user-read-currently-playing",  # Modify permission if you want to control playback through the app
}

URLS = {
  "REDIRECT_URI": "http://localhost:8888/callback",
  "AUTH_URL": f"https://accounts.spotify.com/authorize?{urlencode({ 'client_id': PARAMS['CLIENT_ID'], 'response_type': 'code', 'redirect_uri': 'http://localhost:8888/callback', 'scope': PARAMS['SCOPE'] })}",
  "TOKEN_URL": "https://accounts.spotify.com/api/token",
}

SP = spotipy.Spotify(
  auth_manager=SpotifyOAuth(
    client_id=PARAMS["CLIENT_ID"],
    client_secret=PARAMS["CLIENT_SECRET"],
    redirect_uri=URLS["REDIRECT_URI"],
    scope=PARAMS["SCOPE"],
  )
)

DEF_PREFS = load_json(r"config\preferences_default.json")
USER_PREFS = load_json(r"config\preferences_user.json")
THEMES = load_json(r"config\themes.json")


def get_current_theme(def_p, user_p, themes, theme_name=""):
  # Returns the theme selected by the user
  theme = theme_name
  if theme_name == "":
    theme = user_p.get("theme", def_p.get("theme"))

  if theme == "user": return themes.get("user")
  if theme == "dark": return themes.get("dark")
  if theme == "light": return themes.get("light")

  # Adaptive theme as fallback
  if darkdetect.isDark():
    return themes.get("dark")
  else:
    return themes.get("light")


THEME = get_current_theme(DEF_PREFS, USER_PREFS, THEMES)


def get_nowplaying_txt_path(path):
  if path.startswith("C:\\"):
    return path

  username = os.getlogin()
  if not username:
    username = os.environ.get('USERNAME')

  if not path.endswith(".txt"):
    path += ".txt"

  return f"C:\\Users\\{username}\\AppData\\Roaming\\{path}"


NOWPLAYING_TXT_PATH = get_nowplaying_txt_path(USER_PREFS.get("now_playing_txt_path", DEF_PREFS.get("now_playing_txt_path")))
