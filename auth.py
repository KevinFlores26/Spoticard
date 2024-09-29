import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from spotipy.oauth2 import SpotifyOAuth

from config.config import params as p
from config.config import urls

webbrowser.open(urls["AUTH_URL"])
class RequestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    query_components = parse_qs(self.path.split("?", 1)[-1])
    auth_code = query_components.get("code")

    if auth_code:
      self.send_response(200)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      self.wfile.write(b"Authentication successful! You can close this window.")
      auth_code = auth_code[0]

      # Change the auth code into an access token
      sp_oauth = SpotifyOAuth(
        client_id=p["CLIENT_ID"],
        client_secret=p["CLIENT_SECRET"],
        redirect_uri=urls["REDIRECT_URI"],
      )
      token_info = sp_oauth.get_access_token(auth_code)
      print("Access Token: ", token_info["access_token"])

    else:
      self.send_response(400)
      self.end_headers()
      self.wfile.write(b"Authentication failed.")


server_address = ("", 8888)
httpd = HTTPServer(server_address, RequestHandler)
print("Server running at http://localhost:8888/")
httpd.serve_forever()
